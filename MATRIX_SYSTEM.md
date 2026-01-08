# Matrix System - Complete System as Linear Algebra

## What It Is

Everything (facade, neurocommander, learning) represented as matrix operations on sparse tensors stored in Redis.

## State Vector

Complete system = 599-dimensional vector:
- Windows: [app, x, y, w, h]
- Processes: [pid, cpu, mem]
- Files: [path_hash, mtime, size]
- Facade: [timestamp, hash]

## Key Operations

### 1. Temporal Matrix T[files × time_buckets]
```python
T = system.build_temporal_matrix(window_hours=168)
# Sparse matrix of file modifications over time
```

### 2. Query Work Session
```python
files = system.query_work_session(hours_ago=3)
# "What was I working on 3 hours ago?"
# Returns: Matrix slice + ranking by relevance
```

### 3. File Importance
```python
centrality = system.compute_eigenvector_centrality()
# Frequency-based importance ranking
```

### 4. Work Sessions
```python
sessions = system.svd_work_sessions(k=5)
# Temporal clustering of activity patterns
```

## Why Matrix Form

1. **Differentiable** - Learn optimal window arrangements
2. **Composable** - Chain transformations
3. **Queryable** - Linear algebra on state
4. **Distributable** - Partition the matrix across machines

## Actions as Linear Transformations

```python
# Window move = translation matrix
Move(W, dx, dy) = W + [dx, dy, 0, 0]

# Drag = affine transform
Drag(W, target) = W @ M(target)

# Query = matrix multiplication
get_bounds(app) = W[app] @ I
```

## Redis Storage

- `matrix:states` - State vector stream
- `matrix:temporal:files` - File index
- `matrix:temporal:min_ts` - Time bounds
- `matrix:temporal:bucket_size` - Discretization

## Current State

Captured: 599-dim state
- 0 windows
- 99 processes
- 100 files

Stored in Redis, queryable forever.

## What's Valuable

**"What was I working on 3 hours ago?"** - Actual utility for debugging workflow

All other infrastructure supports this one query.
