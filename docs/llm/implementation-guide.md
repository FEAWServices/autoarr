# AutoArr LLM Implementation Guide

Complete code and scripts for training and deploying your local LLM.

---

## 📁 Project Structure

```
autoarr/
├── llm/                           # LLM training and deployment
│   ├── data/                      # Training data
│   │   ├── raw/                   # Raw scraped documentation
│   │   ├── processed/             # Processed Q&A pairs
│   │   └── train.jsonl            # Training dataset
│   ├── models/                    # Trained models
│   │   ├── base/                  # Base Llama model cache
│   │   └── autoarr-lora/          # Fine-tuned LoRA adapter
│   ├── scripts/                   # Training scripts
│   │   ├── 01_collect_data.py
│   │   ├── 02_generate_qa.py
│   │   ├── 03_train_lora.py
│   │   ├── 04_evaluate.py
│   │   └── 05_convert_gguf.py
│   ├── config/                    # Configuration files
│   │   ├── training_config.yaml
│   │   └── lora_config.yaml
│   └── requirements.txt           # Python dependencies
```

---

## 🔧 Complete Setup Script

**File: `llm/setup.sh`**

```bash
#!/bin/bash
# AutoArr LLM Setup Script

set -e

echo "🚀 Setting up AutoArr LLM environment..."

# Check for GPU
if ! command -v nvidia-smi &> /dev/null; then
    echo "⚠️  Warning: nvidia-smi not found. GPU training may not work."
else
    echo "✅ GPU detected:"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
fi

# Create conda environment
echo "📦 Creating conda environment..."
conda create -n autoarr-llm python=3.10 -y
eval "$(conda shell.bash hook)"
conda activate autoarr-llm

# Install PyTorch with CUDA
echo "🔥 Installing PyTorch..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install training dependencies
echo "📚 Installing training dependencies..."
pip install -r requirements.txt

# Create directories
echo "📁 Creating directory structure..."
mkdir -p data/{raw,processed}
mkdir -p models/{base,autoarr-lora}
mkdir -p logs
mkdir -p vectorstore

# Download base model (if not exists)
echo "📥 Checking for base model..."
if [ ! -d "models/base/Meta-Llama-3.1-8B-Instruct" ]; then
    echo "Downloading base model (this may take a while)..."
    python -c "
from huggingface_hub import snapshot_download
snapshot_download(
    'meta-llama/Meta-Llama-3.1-8B-Instruct',
    local_dir='models/base/Meta-Llama-3.1-8B-Instruct',
    local_dir_use_symlinks=False
)
"
else
    echo "✅ Base model already downloaded"
fi

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. conda activate autoarr-llm"
echo "2. python scripts/01_collect_data.py"
echo "3. python scripts/02_generate_qa.py"
echo "4. python scripts/03_train_lora.py"
```

---

## 📦 Requirements File

**File: `llm/requirements.txt`**

```txt
# Core ML
torch>=2.1.0
transformers>=4.36.0
accelerate>=0.25.0
peft>=0.7.0
bitsandbytes>=0.41.0
trl>=0.7.0

# Data processing
datasets>=2.15.0
pandas>=2.1.0
numpy>=1.24.0

# LangChain
langchain>=0.1.0
langchain-community>=0.0.10
langchain-huggingface>=0.0.1

# Vector store & embeddings
chromadb>=0.4.18
sentence-transformers>=2.2.2

# Web scraping
beautifulsoup4>=4.12.0
requests>=2.31.0
scrapy>=2.11.0

# Model serving
ollama>=0.1.0
vllm>=0.2.0  # Optional, for high-performance serving

# Evaluation
rouge-score>=0.1.2
bert-score>=0.3.13

# Utilities
tqdm>=4.66.0
python-dotenv>=1.0.0
pyyaml>=6.0
wandb>=0.16.0  # For experiment tracking

# API clients (for Q&A generation)
anthropic>=0.7.0

# Format conversion
llama-cpp-python>=0.2.0
gguf>=0.1.0
```

---

## 📊 Data Collection Script

**File: `llm/scripts/01_collect_data.py`**

```python
#!/usr/bin/env python3
"""
Collect documentation from all *arr applications.
"""

import os
import json
import asyncio
from pathlib import Path
from typing import List, Dict
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


class DocumentationScraper:
    """Scrape documentation from various sources."""

    def __init__(self, output_dir: str = "data/raw"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.visited_urls = set()

    def scrape_url(self, url: str, max_depth: int = 2, current_depth: int = 0) -> List[Dict]:
        """Recursively scrape a URL and its links."""

        if current_depth > max_depth or url in self.visited_urls:
            return []

        self.visited_urls.add(url)
        documents = []

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract main content
            # Adjust selectors based on site structure
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')

            if main_content:
                # Extract text
                text = main_content.get_text(separator='\n', strip=True)

                # Get title
                title = soup.find('h1')
                title_text = title.get_text(strip=True) if title else url

                documents.append({
                    'url': url,
                    'title': title_text,
                    'content': text,
                    'depth': current_depth
                })

            # Find and scrape linked pages (same domain only)
            if current_depth < max_depth:
                base_domain = urlparse(url).netloc
                links = soup.find_all('a', href=True)

                for link in links:
                    href = link['href']
                    absolute_url = urljoin(url, href)

                    # Only follow links on same domain
                    if urlparse(absolute_url).netloc == base_domain:
                        documents.extend(
                            self.scrape_url(absolute_url, max_depth, current_depth + 1)
                        )

        except Exception as e:
            print(f"Error scraping {url}: {e}")

        return documents

    def scrape_source(self, name: str, url: str, max_depth: int = 2):
        """Scrape a documentation source."""
        print(f"\n📖 Scraping {name} documentation from {url}")

        docs = self.scrape_url(url, max_depth)

        # Save to file
        output_file = self.output_dir / f"{name.lower()}.jsonl"
        with open(output_file, 'w', encoding='utf-8') as f:
            for doc in docs:
                doc['source'] = name
                f.write(json.dumps(doc, ensure_ascii=False) + '\n')

        print(f"✅ Collected {len(docs)} documents from {name}")
        return len(docs)


def main():
    """Main data collection pipeline."""

    scraper = DocumentationScraper()

    # Define sources
    sources = [
        {
            'name': 'Sonarr',
            'url': 'https://wiki.servarr.com/sonarr',
            'depth': 2
        },
        {
            'name': 'Radarr',
            'url': 'https://wiki.servarr.com/radarr',
            'depth': 2
        },
        {
            'name': 'SABnzbd',
            'url': 'https://sabnzbd.org/wiki/',
            'depth': 2
        },
        {
            'name': 'TRaSH-Guides',
            'url': 'https://trash-guides.info/',
            'depth': 1
        }
    ]

    total_docs = 0

    for source in sources:
        count = scraper.scrape_source(
            source['name'],
            source['url'],
            source['depth']
        )
        total_docs += count

    print(f"\n🎉 Total documents collected: {total_docs}")
    print(f"📁 Saved to: {scraper.output_dir}")


if __name__ == "__main__":
    main()
```

---

## 🤖 Q&A Generation Script

**File: `llm/scripts/02_generate_qa.py`**

````python
#!/usr/bin/env python3
"""
Generate Q&A pairs from collected documentation using Claude.
"""

import os
import json
import asyncio
from pathlib import Path
from typing import List, Dict

from anthropic import Anthropic
from tqdm.asyncio import tqdm_asyncio
from dotenv import load_dotenv

load_dotenv()


class QAGenerator:
    """Generate Q&A pairs from documentation."""

    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
        self.processed_dir = Path("data/processed")
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    async def generate_qa_for_document(self, doc: Dict) -> List[Dict]:
        """Generate Q&A pairs for a single document."""

        prompt = f"""You are an expert in media automation. Given this documentation, generate 5 realistic question-answer pairs that users might ask.

Source: {doc['source']}
Title: {doc['title']}

Documentation:
{doc['content'][:2000]}  # Limit context size

Requirements:
1. Questions should be practical and common
2. Answers should be detailed and actionable
3. Include specific configuration examples where relevant
4. Vary the difficulty (easy to advanced)

Format as JSON array:
[
  {{
    "question": "...",
    "answer": "...",
    "difficulty": "easy|medium|hard",
    "category": "configuration|troubleshooting|optimization|general"
  }}
]

Generate ONLY valid JSON, nothing else."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse JSON response
            content = response.content[0].text

            # Extract JSON (handle markdown code blocks)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            qa_pairs = json.loads(content)

            # Add metadata
            for pair in qa_pairs:
                pair['source'] = doc['source']
                pair['source_url'] = doc['url']
                pair['source_title'] = doc['title']

            return qa_pairs

        except Exception as e:
            print(f"Error generating Q&A for {doc['title']}: {e}")
            return []

    async def process_documents(self, input_file: Path, batch_size: int = 5):
        """Process all documents in a file."""

        # Load documents
        documents = []
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                documents.append(json.loads(line))

        print(f"Processing {len(documents)} documents from {input_file.name}")

        # Process in batches to respect rate limits
        all_qa_pairs = []

        for i in tqdm_asyncio(range(0, len(documents), batch_size)):
            batch = documents[i:i + batch_size]

            # Process batch
            tasks = [self.generate_qa_for_document(doc) for doc in batch]
            results = await asyncio.gather(*tasks)

            for qa_list in results:
                all_qa_pairs.extend(qa_list)

            # Rate limiting (Claude has 60 req/min limit)
            if i + batch_size < len(documents):
                await asyncio.sleep(6)  # 10 requests per minute

        return all_qa_pairs

    def save_training_data(self, qa_pairs: List[Dict], output_file: str):
        """Save Q&A pairs in training format."""

        output_path = self.processed_dir / output_file

        with open(output_path, 'w', encoding='utf-8') as f:
            for qa in qa_pairs:
                # Convert to instruction format
                training_example = {
                    "instruction": qa['question'],
                    "input": "",
                    "output": qa['answer'],
                    "metadata": {
                        "source": qa['source'],
                        "difficulty": qa.get('difficulty', 'medium'),
                        "category": qa.get('category', 'general')
                    }
                }
                f.write(json.dumps(training_example, ensure_ascii=False) + '\n')

        print(f"✅ Saved {len(qa_pairs)} training examples to {output_path}")


async def main():
    """Main Q&A generation pipeline."""

    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable required")

    generator = QAGenerator(api_key)

    # Process each documentation source
    raw_dir = Path("data/raw")
    all_qa_pairs = []

    for input_file in raw_dir.glob("*.jsonl"):
        print(f"\n📝 Processing {input_file.name}...")
        qa_pairs = await generator.process_documents(input_file)
        all_qa_pairs.extend(qa_pairs)

    # Save all training data
    generator.save_training_data(all_qa_pairs, "train.jsonl")

    print(f"\n🎉 Generated {len(all_qa_pairs)} total Q&A pairs")
    print(f"📁 Training data saved to: data/processed/train.jsonl")


if __name__ == "__main__":
    asyncio.run(main())
````

---

## 🏋️ LoRA Training Script

**File: `llm/scripts/03_train_lora.py`**

```python
#!/usr/bin/env python3
"""
Train LoRA adapter on AutoArr documentation.
"""

import os
import torch
from pathlib import Path
from dataclasses import dataclass

from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import load_dataset
from trl import SFTTrainer


@dataclass
class Config:
    """Training configuration."""

    # Model
    base_model: str = "models/base/Meta-Llama-3.1-8B-Instruct"
    output_dir: str = "models/autoarr-lora"

    # Data
    train_file: str = "data/processed/train.jsonl"

    # LoRA config
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05

    # Training
    num_epochs: int = 3
    batch_size: int = 4
    gradient_accumulation_steps: int = 4
    learning_rate: float = 2e-4
    max_seq_length: int = 2048

    # Hardware
    fp16: bool = True
    bf16: bool = False


def format_instruction(example: dict) -> str:
    """Format example in Llama 3.1 chat format."""

    return f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are an expert in media automation using SABnzbd, Sonarr, Radarr, and Plex.
Provide helpful, accurate, and concise advice based on official documentation and best practices.<|eot_id|><|start_header_id|>user<|end_header_id|>

{example['instruction']}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

{example['output']}<|eot_id|>"""


def train():
    """Run LoRA training."""

    config = Config()

    print("🚀 Starting LoRA training...")
    print(f"📂 Base model: {config.base_model}")
    print(f"📊 Training file: {config.train_file}")
    print(f"💾 Output directory: {config.output_dir}")

    # Load tokenizer
    print("\n📝 Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(config.base_model)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    # Quantization config
    print("🔢 Configuring 4-bit quantization...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    # Load base model
    print("📦 Loading base model (this may take a few minutes)...")
    model = AutoModelForCausalLM.from_pretrained(
        config.base_model,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )

    # Prepare for training
    print("⚙️  Preparing model for training...")
    model = prepare_model_for_kbit_training(model)

    # LoRA config
    print("🎯 Applying LoRA configuration...")
    lora_config = LoraConfig(
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
        lora_dropout=config.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM"
    )

    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # Load dataset
    print(f"\n📚 Loading training data from {config.train_file}...")
    dataset = load_dataset("json", data_files=config.train_file)

    print(f"✅ Loaded {len(dataset['train'])} training examples")

    # Training arguments
    training_args = TrainingArguments(
        output_dir=config.output_dir,
        num_train_epochs=config.num_epochs,
        per_device_train_batch_size=config.batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        learning_rate=config.learning_rate,
        fp16=config.fp16,
        bf16=config.bf16,
        logging_steps=10,
        save_strategy="epoch",
        save_total_limit=3,
        warmup_ratio=0.1,
        lr_scheduler_type="cosine",
        optim="paged_adamw_8bit",
        report_to="wandb",  # Change to "none" if not using wandb
    )

    # Create trainer
    print("\n🏋️  Creating trainer...")
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset["train"],
        tokenizer=tokenizer,
        formatting_func=format_instruction,
        max_seq_length=config.max_seq_length,
    )

    # Train!
    print("\n🚀 Starting training...\n")
    trainer.train()

    # Save final model
    print("\n💾 Saving model...")
    trainer.save_model(config.output_dir)
    tokenizer.save_pretrained(config.output_dir)

    print(f"\n✅ Training complete!")
    print(f"📂 Model saved to: {config.output_dir}")


if __name__ == "__main__":
    train()
```

---

## 🧪 Evaluation Script

**File: `llm/scripts/04_evaluate.py`**

```python
#!/usr/bin/env python3
"""
Evaluate trained model on test set.
"""

import json
import torch
from pathlib import Path
from typing import List, Tuple

from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from rouge_score import rouge_scorer
from tqdm import tqdm


class ModelEvaluator:
    """Evaluate model performance."""

    def __init__(self, base_model_path: str, lora_path: str):
        print("Loading model...")

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(base_model_path)

        # Load base model
        self.model = AutoModelForCausalLM.from_pretrained(
            base_model_path,
            torch_dtype=torch.float16,
            device_map="auto"
        )

        # Load LoRA adapter
        self.model = PeftModel.from_pretrained(self.model, lora_path)
        self.model.eval()

        # ROUGE scorer
        self.rouge = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)

    def generate_answer(self, question: str, max_length: int = 512) -> str:
        """Generate answer to a question."""

        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are an expert in media automation using SABnzbd, Sonarr, Radarr, and Plex.
Provide helpful, accurate, and concise advice.<|eot_id|><|start_header_id|>user<|end_header_id|>

{question}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_length,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )

        # Decode and extract answer
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract just the assistant's response
        if "<|start_header_id|>assistant<|end_header_id|>" in response:
            answer = response.split("<|start_header_id|>assistant<|end_header_id|>")[-1]
            answer = answer.split("<|eot_id|>")[0].strip()
            return answer

        return response

    def evaluate_dataset(self, test_file: str) -> dict:
        """Evaluate on test dataset."""

        print(f"Loading test data from {test_file}...")

        # Load test data
        with open(test_file, 'r') as f:
            test_data = [json.loads(line) for line in f]

        print(f"Evaluating on {len(test_data)} examples...")

        rouge_scores = []
        predictions = []
        references = []

        for example in tqdm(test_data):
            question = example['instruction']
            reference = example['output']

            # Generate prediction
            prediction = self.generate_answer(question)

            predictions.append(prediction)
            references.append(reference)

            # Calculate ROUGE
            scores = self.rouge.score(reference, prediction)
            rouge_scores.append(scores)

        # Calculate averages
        avg_rouge1 = sum(s['rouge1'].fmeasure for s in rouge_scores) / len(rouge_scores)
        avg_rouge2 = sum(s['rouge2'].fmeasure for s in rouge_scores) / len(rouge_scores)
        avg_rougeL = sum(s['rougeL'].fmeasure for s in rouge_scores) / len(rouge_scores)

        results = {
            'rouge1': avg_rouge1,
            'rouge2': avg_rouge2,
            'rougeL': avg_rougeL,
            'num_examples': len(test_data)
        }

        return results, predictions, references


def main():
    """Run evaluation."""

    base_model = "models/base/Meta-Llama-3.1-8B-Instruct"
    lora_path = "models/autoarr-lora"
    test_file = "data/processed/test.jsonl"

    evaluator = ModelEvaluator(base_model, lora_path)

    results, predictions, references = evaluator.evaluate_dataset(test_file)

    print("\n📊 Evaluation Results:")
    print(f"ROUGE-1: {results['rouge1']:.4f}")
    print(f"ROUGE-2: {results['rouge2']:.4f}")
    print(f"ROUGE-L: {results['rougeL']:.4f}")
    print(f"Examples: {results['num_examples']}")

    # Save results
    output_file = "evaluation_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Results saved to {output_file}")


if __name__ == "__main__":
    main()
```

---

## 🎯 Quick Start Commands

```bash
# 1. Setup environment
bash llm/setup.sh

# 2. Activate environment
conda activate autoarr-llm

# 3. Set API key for Q&A generation
export ANTHROPIC_API_KEY=your_key_here

# 4. Run complete pipeline
cd llm

# Collect documentation (10-20 minutes)
python scripts/01_collect_data.py

# Generate Q&A pairs (1-2 hours, costs ~$5-10 in API calls)
python scripts/02_generate_qa.py

# Train LoRA adapter (2-4 hours on RTX 4090)
python scripts/03_train_lora.py

# Evaluate model (30 minutes)
python scripts/04_evaluate.py

# Deploy with Ollama
ollama create autoarr -f Modelfile
ollama serve
```

---

## 📝 Usage in AutoArr API

**File: `api/intelligence/local_llm.py`**

```python
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain


class LocalLLMAgent:
    """LLM agent using local Ollama model."""

    def __init__(self, model_name: str = "autoarr", fallback_to_claude: bool = True):
        self.model_name = model_name
        self.fallback_to_claude = fallback_to_claude

        try:
            self.llm = Ollama(
                model=model_name,
                base_url="http://localhost:11434",
                temperature=0.7
            )
        except Exception as e:
            if fallback_to_claude:
                print(f"Failed to load local model, falling back to Claude: {e}")
                from anthropic import Anthropic
                self.llm = Anthropic()
            else:
                raise

    async def analyze_configuration(
        self,
        app_name: str,
        config: dict,
        best_practices: list
    ) -> str:
        """Analyze configuration and recommend improvements."""

        prompt = PromptTemplate(
            template="""Analyze this {app_name} configuration:

{config}

Best practices:
{practices}

Provide specific recommendations with priorities (high/medium/low).""",
            input_variables=["app_name", "config", "practices"]
        )

        chain = LLMChain(llm=self.llm, prompt=prompt)

        return await chain.ainvoke({
            "app_name": app_name,
            "config": str(config),
            "practices": "\n".join(best_practices)
        })
```

---

_This guide provides everything you need to train and deploy your own local LLM for AutoArr!_
