#!/usr/bin/env python3
"""
Complete system as matrix operations.
Everything is linear algebra on sparse tensors in Redis.
"""

import redis
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

try:
    import numpy as np
    HAS_NUMPY = True
except:
    HAS_NUMPY = False
    # Pure Python fallback
    class np:
        @staticmethod
        def array(x): return x
        @staticmethod
        def zeros(shape): return [[0]*shape[1] for _ in range(shape[0])] if len(shape) > 1 else [0]*shape[0]
        @staticmethod
        def concatenate(arrays):
            result = []
            for arr in arrays: result.extend(arr if isinstance(arr, list) else [arr])
            return result

@dataclass
class StateVector:
    """Complete system state as vector"""
    timestamp: float
    windows: list      # [app, x, y, w, h]
    processes: list    # [pid, cpu, mem]
    files: list        # [path_hash, mtime, size]
    facade: list       # [property, value]

    def to_vector(self) -> list:
        """Flatten to single state vector"""
        result = []
        for row in self.windows: result.extend(row)
        for row in self.processes: result.extend(row)
        for row in self.files: result.extend(row)
        result.extend(self.facade)
        return result

    def dimension(self) -> int:
        return len(self.to_vector())


class MatrixSystem:
    """Complete system represented as matrix operations"""

    def __init__(self):
        self.redis = redis.Redis(decode_responses=True)

        # State matrices (sparse)
        self.W = None  # Window state [apps x properties]
        self.P = None  # Process state [pids x properties]
        self.F = None  # File state [files x properties]
        self.S = None  # System state [timestamps x state_dim]

        # Learned matrices
        self.V = None  # Value function [state x 1]
        self.T = None  # Transition model [state x action x state]

        # Index mappings
        self.app_index = {}
        self.pid_index = {}
        self.file_index = {}

    def capture_state(self) -> StateVector:
        """Capture complete system state as vector"""
        import subprocess

        timestamp = datetime.now().timestamp()

        # Get window state via neurocommander
        try:
            result = subprocess.run(
                ['redis-ai-challenge/neurocommander.sh', 'update'],
                capture_output=True, text=True, timeout=5
            )
        except:
            pass

        # Build window matrix
        windows = []
        window_keys = self.redis.hkeys('neuro:windows:current')
        for key in window_keys:
            if ':bounds' in key:
                app = key.replace(':bounds', '')
                bounds = self.redis.hget('neuro:windows:current', key)
                if bounds:
                    x1, y1, x2, y2 = map(int, bounds.split(','))
                    windows.append([x1, y1, x2-x1, y2-y1])
                    if app not in self.app_index:
                        self.app_index[app] = len(self.app_index)

        W = windows if windows else []

        # Build process matrix (simplified)
        ps_output = subprocess.run(
            ['ps', 'aux'], capture_output=True, text=True
        ).stdout.split('\n')[1:100]  # First 100 processes

        processes = []
        for line in ps_output:
            if line.strip():
                parts = line.split()
                if len(parts) >= 11:
                    try:
                        pid = int(parts[1])
                        cpu = float(parts[2])
                        mem = float(parts[3])
                        processes.append([pid, cpu, mem])
                    except:
                        pass

        P = processes if processes else []

        # Build file matrix (recently modified in ~/src)
        try:
            files_output = subprocess.run(
                ['find', '/Users/jonathanhill/src/redis-ai-challenge', '-type', 'f',
                 '-mtime', '-7'],
                capture_output=True, text=True, timeout=3
            ).stdout.split('\n')[:100]  # First 100 files
        except:
            files_output = []

        files = []
        for filepath in files_output:
            if filepath.strip():
                try:
                    import os
                    stat = os.stat(filepath)
                    path_hash = hash(filepath) % (2**31)
                    files.append([path_hash, stat.st_mtime, stat.st_size])
                    if filepath not in self.file_index:
                        self.file_index[filepath] = len(self.file_index)
                except:
                    pass

        F = files if files else []

        # Facade state from Redis
        facade_data = self.redis.get('facade:test:frontmost')
        facade = [timestamp, hash(facade_data or '') % 1000]

        state = StateVector(
            timestamp=timestamp,
            windows=W,
            processes=P,
            files=F,
            facade=facade
        )

        # Store in Redis as JSON
        self.redis.xadd('matrix:states', {
            'timestamp': timestamp,
            'state_dim': state.dimension(),
            'windows': len(W),
            'processes': len(P),
            'files': len(F)
        })

        return state

    def build_temporal_matrix(self, window_hours: int = 24) -> dict:
        """Build temporal matrix T[files x timestamps]
        Returns dict representation since we don't have scipy"""
        # Query recent file modifications
        import subprocess
        from datetime import datetime, timedelta

        cutoff = (datetime.now() - timedelta(hours=window_hours)).timestamp()

        try:
            files_output = subprocess.run(
                ['find', '/Users/jonathanhill/src/redis-ai-challenge', '-type', 'f',
                 '-mtime', f'-{window_hours//24 + 1}',
                 '-exec', 'stat', '-f', '%Sm|%N', '-t', '%s', '{}', ';'],
                capture_output=True, text=True, timeout=5
            ).stdout.strip().split('\n')
        except:
            files_output = []

        # Build sparse matrix
        n_files = 0
        timestamps = []
        file_to_idx = {}

        for line in files_output[:1000]:  # Limit to 1000 files
            if '|' in line:
                ts_str, filepath = line.split('|', 1)
                try:
                    ts = float(ts_str)
                    if ts >= cutoff:
                        if filepath not in file_to_idx:
                            file_to_idx[filepath] = len(file_to_idx)
                        timestamps.append((file_to_idx[filepath], ts))
                except:
                    pass

        n_files = len(file_to_idx)
        if n_files == 0:
            return {'shape': (0, 0), 'data': {}}

        # Discretize time into buckets
        min_ts = min(t for _, t in timestamps)
        max_ts = max(t for _, t in timestamps)
        n_buckets = 100
        bucket_size = (max_ts - min_ts) / n_buckets if max_ts > min_ts else 1

        # Sparse matrix as dict
        T = {}
        for file_idx, ts in timestamps:
            bucket = int((ts - min_ts) / bucket_size)
            if bucket < n_buckets:
                T[(file_idx, bucket)] = 1

        # Store metadata
        self.redis.set('matrix:temporal:files', json.dumps(list(file_to_idx.keys())))
        self.redis.set('matrix:temporal:min_ts', min_ts)
        self.redis.set('matrix:temporal:bucket_size', bucket_size)

        return {
            'shape': (n_files, n_buckets),
            'data': T,
            'files': list(file_to_idx.keys())
        }

    def query_work_session(self, hours_ago: float) -> List[str]:
        """Query: What was I working on N hours ago?

        Returns files ranked by relevance to that time.
        """
        T = self.build_temporal_matrix(window_hours=int(hours_ago * 2))

        if T['shape'][0] == 0:
            return []

        # Get time bucket
        min_ts = float(self.redis.get('matrix:temporal:min_ts') or 0)
        bucket_size = float(self.redis.get('matrix:temporal:bucket_size') or 1)
        target_ts = datetime.now().timestamp() - (hours_ago * 3600)
        target_bucket = int((target_ts - min_ts) / bucket_size)

        if target_bucket < 0 or target_bucket >= T['shape'][1]:
            return []

        # Count activity near that time bucket
        relevance = {}
        for (file_idx, bucket), val in T['data'].items():
            if abs(bucket - target_bucket) <= 2:  # 2-bucket window
                relevance[file_idx] = relevance.get(file_idx, 0) + val

        # Rank files
        files = T['files']
        ranked = sorted(
            [(files[idx], score) for idx, score in relevance.items()],
            key=lambda x: x[1],
            reverse=True
        )

        return [f for f, score in ranked][:20]

    def compute_eigenvector_centrality(self) -> Dict[str, float]:
        """Compute file importance via simple heuristic (frequency)"""
        T = self.build_temporal_matrix()

        if T['shape'][0] == 0:
            return {}

        # Simple centrality = total activity across time
        centrality = {}
        for (file_idx, _), val in T['data'].items():
            centrality[file_idx] = centrality.get(file_idx, 0) + val

        files = T['files']
        # Normalize
        total = sum(centrality.values()) or 1
        return {files[idx]: score/total for idx, score in centrality.items()}

    def svd_work_sessions(self, k: int = 5) -> dict:
        """Extract work sessions (simplified without scipy)

        Returns summary of activity patterns.
        """
        T = self.build_temporal_matrix()

        if T['shape'][0] == 0:
            return {}

        # Simple clustering by time
        time_clusters = {}
        for (file_idx, bucket), val in T['data'].items():
            if bucket not in time_clusters:
                time_clusters[bucket] = []
            time_clusters[bucket].append(file_idx)

        # Return top k time periods by activity
        ranked_periods = sorted(
            time_clusters.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:k]

        files = T['files']
        sessions = {}
        for bucket, file_indices in ranked_periods:
            sessions[f"session_{bucket}"] = [files[idx] for idx in file_indices[:10]]

        return sessions

    def demo(self):
        """Demonstrate matrix system"""
        print("=== Matrix System Demo ===\n")

        # Capture current state
        print("1. Capturing state vector...")
        state = self.capture_state()
        print(f"   State dimension: {state.dimension()}")
        print(f"   Windows: {len(state.windows)}")
        print(f"   Processes: {len(state.processes)}")
        print(f"   Files: {len(state.files)}\n")

        # Build temporal matrix
        print("2. Building temporal matrix...")
        T = self.build_temporal_matrix(window_hours=168)  # 1 week
        print(f"   T shape: {T['shape']} (files x time_buckets)")
        print(f"   Non-zero entries: {len(T['data'])}\n")

        # Query work sessions
        print("3. Query: What was I working on 3 hours ago?")
        files = self.query_work_session(hours_ago=3)
        for i, f in enumerate(files[:10]):
            print(f"   {i+1}. {f}")
        print()

        # Eigenvector centrality
        print("4. File importance (eigenvector centrality):")
        centrality = self.compute_eigenvector_centrality()
        top_files = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:10]
        for f, score in top_files:
            print(f"   {score:.4f} - {f}")
        print()

        # SVD work sessions
        print("5. Principal work sessions:")
        sessions = self.svd_work_sessions(k=3)
        if sessions:
            print(f"   Extracted {len(sessions)} work sessions")
            for session_name, files in list(sessions.items())[:3]:
                print(f"   {session_name}: {len(files)} files")
        print()

        print("✅ All operations completed")
        print(f"   Stored in Redis streams: matrix:states, matrix:temporal:*")


if __name__ == '__main__':
    system = MatrixSystem()
    system.demo()
