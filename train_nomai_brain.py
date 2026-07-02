import os
import glob
import pickle
import random
import nltk
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag

class MarkovBrainTrainer:
    def __init__(self, directory, state_size=2):
        self.directory = directory
        self.state_size = state_size
        self.words = []
        self.starts = []
        self.chain = {}
        self._download_nltk_data()

    def _download_nltk_data(self):
        try:
            nltk.data.find('tokenizers/punkt')
        except nltk.downloader.DownloadError:
            nltk.download('punkt', quiet=True)
        try:
            nltk.data.find('taggers/averaged_perceptron_tagger')
        except nltk.downloader.DownloadError:
            nltk.download('averaged_perceptron_tagger', quiet=True)
        print("NLTK data checked/downloaded.")

    def build_corpus(self):
        print(f"Building corpus from: {self.directory}")
        for filepath in glob.glob(os.path.join(self.directory, '**/*.py'), recursive=True):
            if os.path.basename(filepath) in ["train_nomai_brain.py", "nomai_agent.py"]:
                continue # Exclude self and agent to avoid bias

            with open(filepath, 'r', errors='ignore') as f:
                content = f.read()
                file_words = word_tokenize(content) # Use NLTK tokenizer
                self.words.extend(file_words)

    def train(self):
        if not self.words:
            print("Corpus is empty. Build corpus first.")
            return

        for i in range(len(self.words) - self.state_size):
            state = tuple(self.words[i:i+self.state_size])
            next_word = self.words[i+self.state_size]

            if state not in self.chain:
                self.chain[state] = []
            self.chain[state].append(next_word)

            if i < len(self.words) - self.state_size * 2: # Capture enough initial states for generation
                self.starts.append(state)

        print(f"Brain trained with {len(self.chain)} states and {len(self.starts)} start states.")

    def save_brain(self, brain_path):
        with open(brain_path, 'wb') as f:
            pickle.dump({'starts': self.starts, 'chain': self.chain}, f)
        print(f"Brain saved to {brain_path}")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    trainer = MarkovBrainTrainer(script_dir)
    trainer.build_corpus()
    trainer.train()
    trainer.save_brain(os.path.join(script_dir, "nomai_brain.pkl"))