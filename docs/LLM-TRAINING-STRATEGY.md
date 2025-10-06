# AutoArr Local LLM Strategy

## Executive Summary

This document outlines the strategy for training and deploying a specialized LLM for AutoArr using **local infrastructure** (not cloud-hosted) with LangChain integration.

**Recommended Approach:**
- **Base Model:** Llama 3.1 8B Instruct (or Llama 3.2 3B for lower resource requirements)
- **Training Method:** LoRA (Low-Rank Adaptation) fine-tuning
- **Framework:** LangChain + Hugging Face Transformers
- **Deployment:** Ollama for easy local serving
- **Training Data:** Curated *arr documentation + community knowledge

---

## 🎯 Model Selection

### Recommended: Llama 3.1 8B Instruct

**Why This Model:**
- ✅ **Open Source**: Fully permissive commercial license
- ✅ **Right Size**: 8B parameters - powerful but runnable on consumer hardware
- ✅ **Instruction-Tuned**: Already trained to follow instructions
- ✅ **Context Window**: 128K tokens (huge for documentation)
- ✅ **Quality**: Matches GPT-3.5 quality on many tasks
- ✅ **Community Support**: Extensive tooling and examples

**Hardware Requirements:**
- **Minimum**: 16GB RAM, 10GB VRAM (GPU)
- **Recommended**: 32GB RAM, 16GB+ VRAM (RTX 4090, A4000, etc.)
- **Training**: 24GB+ VRAM recommended (or use parameter-efficient methods)

### Alternative: Llama 3.2 3B Instruct

**For Lower Resources:**
- 🔹 **Smaller**: 3B parameters
- 🔹 **Faster**: Quicker inference
- 🔹 **Hardware**: Runs on 8GB VRAM
- 🔹 **Trade-off**: Slightly lower quality reasoning

**Hardware Requirements:**
- **Minimum**: 8GB RAM, 6GB VRAM
- **Recommended**: 16GB RAM, 8GB VRAM

### Other Options Considered

| Model | Size | Pros | Cons | Verdict |
|-------|------|------|------|---------|
| Mistral 7B | 7B | Fast, high quality | License restrictions | ⚠️ Check license |
| Phi-3 Medium | 14B | Microsoft backed | Larger size | 🔹 Alternative |
| Gemma 2 9B | 9B | Google backed | Newer, less tested | 🔹 Alternative |
| Qwen 2.5 7B | 7B | Strong reasoning | Less documentation | 🔹 Alternative |

---

## 🏗️ Training Architecture

### Phase 1: Domain Adaptation (Recommended)

**Objective:** Teach the model *arr ecosystem knowledge

**Method:** Continued Pre-training + LoRA Fine-tuning

```
Base Model (Llama 3.1 8B)
    ↓
Continued Pre-training on *arr docs (optional)
    ↓
LoRA Fine-tuning on Q&A pairs
    ↓
Specialized AutoArr Model
```

### Training Data Sources

#### 1. Official Documentation (Curated)
- SABnzbd wiki and docs
- Sonarr wiki (servarr.com)
- Radarr wiki (servarr.com)
- Plex support articles
- API documentation for all apps

**Collection Method:**
```python
# Use web scraping + cleaning
from langchain.document_loaders import RecursiveUrlLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Example: Scrape Sonarr docs
loader = RecursiveUrlLoader(
    url="https://wiki.servarr.com/sonarr",
    max_depth=3
)
docs = loader.load()

# Clean and chunk
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
chunks = text_splitter.split_documents(docs)
```

#### 2. Community Knowledge
- Reddit r/sonarr, r/radarr top posts
- Discord server FAQs
- GitHub issues (resolved questions)
- TRaSH Guides (https://trash-guides.info/)

#### 3. Synthetic Q&A Generation
- Use Claude/GPT-4 to generate Q&A pairs from documentation
- Creates training data in instruction format

**Example Generation Prompt:**
```
Given this documentation about Sonarr configuration:
[DOCUMENTATION]

Generate 5 realistic question-answer pairs that a user might ask.
Format as:
Q: [question]
A: [detailed answer based on documentation]
```

### Training Dataset Structure

**Target Size:** 10,000-50,000 instruction examples

```json
{
  "instruction": "What is the optimal download directory structure for SABnzbd?",
  "input": "",
  "output": "The optimal structure is to have separate directories:\n1. Download Dir: /downloads/complete\n2. Incomplete Dir: /downloads/incomplete\n3. This prevents issues with media managers trying to import incomplete files and allows SABnzbd to handle cleanup properly. You should also ensure these directories have proper permissions (typically 755 for directories, 644 for files)."
}
```

---

## 🔧 Training Implementation

### Setup: Local Training Environment

**Hardware Setup:**
```bash
# Required: CUDA-capable GPU
nvidia-smi  # Verify GPU

# Recommended: Ubuntu 22.04 or similar
# Python 3.10+
```

**Software Stack:**
```bash
# Create conda environment
conda create -n autoarr-training python=3.10
conda activate autoarr-training

# Install dependencies
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install transformers accelerate peft bitsandbytes
pip install langchain langchain-community
pip install datasets huggingface_hub
pip install wandb  # For experiment tracking
```

### Method 1: LoRA Fine-Tuning (Recommended)

**Why LoRA:**
- ✅ **Efficient**: Train only 0.1-1% of parameters
- ✅ **Fast**: 2-4 hours on single GPU
- ✅ **Low Memory**: Can train on 16GB VRAM
- ✅ **Switchable**: Can load/unload adapters

**Implementation:**

```python
# train_lora.py
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import load_dataset
from trl import SFTTrainer

# Configuration
MODEL_NAME = "meta-llama/Meta-Llama-3.1-8B-Instruct"
OUTPUT_DIR = "./autoarr-llama-lora"

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
tokenizer.pad_token = tokenizer.eos_token

# Quantization config (reduces memory usage)
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)

# Load base model
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True,
)

# Prepare for training
model = prepare_model_for_kbit_training(model)

# LoRA configuration
lora_config = LoraConfig(
    r=16,  # Rank
    lora_alpha=32,  # Scaling factor
    target_modules=[
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj",
    ],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

# Apply LoRA
model = get_peft_model(model, lora_config)

# Load your dataset
dataset = load_dataset("json", data_files="autoarr_training_data.jsonl")

# Format dataset
def format_instruction(example):
    return f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are an expert in media automation using SABnzbd, Sonarr, Radarr, and Plex. Provide helpful, accurate advice.<|eot_id|><|start_header_id|>user<|end_header_id|>

{example['instruction']}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

{example['output']}<|eot_id|>"""

# Training arguments
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    fp16=True,
    logging_steps=10,
    save_strategy="epoch",
    warmup_ratio=0.1,
    lr_scheduler_type="cosine",
    optim="paged_adamw_8bit",
)

# Create trainer
trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset["train"],
    tokenizer=tokenizer,
    formatting_func=format_instruction,
    max_seq_length=2048,
)

# Train!
trainer.train()

# Save LoRA adapter
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)
```

**Training Time:**
- **8B model with LoRA**: 2-4 hours on RTX 4090
- **3B model with LoRA**: 1-2 hours on RTX 4090

### Method 2: Full Fine-Tuning (If You Have Resources)

**Requirements:**
- 40GB+ VRAM (A100, multiple GPUs)
- 8-12 hours training time

**Only recommended if:**
- You have access to high-end GPU cluster
- You want absolute maximum quality
- You're training on 100K+ examples

---

## 🚀 Deployment Strategy

### Option 1: Ollama (Recommended)

**Why Ollama:**
- ✅ **Easy**: One command to serve models
- ✅ **OpenAI-compatible API**: Drop-in replacement
- ✅ **Efficient**: Optimized inference
- ✅ **Multi-model**: Switch models easily

**Setup:**

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Convert your LoRA model to GGUF format
pip install llama-cpp-python

# Create Modelfile
cat > Modelfile << 'EOF'
FROM ./autoarr-llama.gguf

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40

SYSTEM You are an expert in media automation using SABnzbd, Sonarr, Radarr, and Plex. Provide helpful, accurate, and concise advice.
EOF

# Create Ollama model
ollama create autoarr -f Modelfile

# Run the model
ollama run autoarr
```

**Usage in AutoArr:**

```python
# api/intelligence/llm_agent.py
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate

class LocalLLMAgent:
    """LLM Agent using locally hosted Ollama."""
    
    def __init__(self, model_name: str = "autoarr"):
        self.llm = Ollama(
            model=model_name,
            base_url="http://localhost:11434",
            temperature=0.7
        )
    
    async def analyze_configuration(
        self,
        app_name: str,
        config: dict,
        best_practices: list
    ) -> str:
        """Analyze configuration and provide recommendations."""
        
        prompt = PromptTemplate(
            template="""Analyze this {app_name} configuration and recommend improvements.

Current Configuration:
{config}

Known Best Practices:
{best_practices}

Provide specific, actionable recommendations with priorities (high/medium/low) and reasons.""",
            input_variables=["app_name", "config", "best_practices"]
        )
        
        chain = prompt | self.llm
        
        return await chain.ainvoke({
            "app_name": app_name,
            "config": str(config),
            "best_practices": "\n".join(best_practices)
        })
```

### Option 2: vLLM Server

**Why vLLM:**
- ✅ **Fast**: State-of-the-art inference speed
- ✅ **Scalable**: Handles concurrent requests well
- ✅ **OpenAI-compatible**: Same API format

**Setup:**

```bash
# Install vLLM
pip install vllm

# Run server
python -m vllm.entrypoints.openai.api_server \
    --model ./autoarr-llama-lora \
    --host 0.0.0.0 \
    --port 8000
```

### Option 3: Hugging Face Transformers (Direct)

**For Maximum Control:**

```python
# api/intelligence/local_model.py
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

class DirectLLM:
    """Direct model loading with transformers."""
    
    def __init__(self, base_model: str, lora_path: str):
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(base_model)
        
        # Load base model
        self.model = AutoModelForCausalLM.from_pretrained(
            base_model,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        
        # Load LoRA adapter
        self.model = PeftModel.from_pretrained(
            self.model,
            lora_path
        )
    
    def generate(self, prompt: str, max_length: int = 512) -> str:
        """Generate response."""
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_length,
            temperature=0.7,
            top_p=0.9,
            do_sample=True
        )
        
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
```

---

## 🔗 LangChain Integration

### RAG (Retrieval-Augmented Generation) Setup

**Why RAG:**
- Provides up-to-date information
- Reduces hallucination
- Allows model to cite sources

**Implementation:**

```python
# api/intelligence/rag_system.py
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_community.llms import Ollama

class AutoArrRAG:
    """RAG system for AutoArr documentation."""
    
    def __init__(self):
        # Initialize embeddings (runs locally)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Initialize vector store
        self.vectorstore = Chroma(
            persist_directory="./chroma_db",
            embedding_function=self.embeddings
        )
        
        # Initialize LLM
        self.llm = Ollama(model="autoarr")
        
        # Create retrieval chain
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(
                search_kwargs={"k": 3}
            )
        )
    
    def add_documents(self, documents: list):
        """Add documentation to vector store."""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        splits = text_splitter.split_documents(documents)
        self.vectorstore.add_documents(splits)
    
    async def query(self, question: str) -> str:
        """Query the RAG system."""
        return await self.qa_chain.ainvoke(question)
```

### Web Search Integration

```python
# api/intelligence/web_search_agent.py
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate

class WebSearchAgent:
    """Agent that can search web for latest best practices."""
    
    def __init__(self):
        self.llm = Ollama(model="autoarr")
        
        # Define tools
        tools = [
            Tool(
                name="SearchDocs",
                func=self._search_docs,
                description="Search official documentation"
            ),
            Tool(
                name="SearchCommunity",
                func=self._search_community,
                description="Search community forums and guides"
            )
        ]
        
        # Create agent
        prompt = PromptTemplate.from_template(
            """You are an expert assistant helping with media automation.
            
            Use these tools to find the most up-to-date information:
            {tools}
            
            Question: {input}
            {agent_scratchpad}"""
        )
        
        agent = create_react_agent(self.llm, tools, prompt)
        self.executor = AgentExecutor(agent=agent, tools=tools)
    
    async def research(self, query: str) -> str:
        """Research a topic using available tools."""
        return await self.executor.ainvoke({"input": query})
```

---

## 📊 Training Data Preparation

### Step-by-Step Data Collection

**Script: `scripts/prepare_training_data.py`**

```python
import json
import asyncio
from langchain.document_loaders import (
    RecursiveUrlLoader,
    GitbookLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from anthropic import Anthropic

async def collect_documentation():
    """Collect documentation from all sources."""
    
    sources = [
        {
            "name": "Sonarr",
            "url": "https://wiki.servarr.com/sonarr",
            "depth": 3
        },
        {
            "name": "Radarr",
            "url": "https://wiki.servarr.com/radarr",
            "depth": 3
        },
        {
            "name": "SABnzbd",
            "url": "https://sabnzbd.org/wiki/",
            "depth": 2
        }
    ]
    
    all_docs = []
    
    for source in sources:
        print(f"Collecting {source['name']} documentation...")
        loader = RecursiveUrlLoader(
            url=source["url"],
            max_depth=source["depth"]
        )
        docs = loader.load()
        
        # Add metadata
        for doc in docs:
            doc.metadata["source_app"] = source["name"]
        
        all_docs.extend(docs)
    
    return all_docs

async def generate_qa_pairs(documentation: list) -> list:
    """Generate Q&A pairs from documentation using Claude."""
    
    client = Anthropic()
    qa_pairs = []
    
    for doc in documentation:
        # Generate Q&A pairs
        prompt = f"""Given this documentation about {doc.metadata['source_app']}:

{doc.page_content}

Generate 3 realistic question-answer pairs that a user might ask.
Format as JSON:
[
  {{"question": "...", "answer": "..."}},
  ...
]

Make answers detailed and practical."""

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse and add to dataset
        pairs = json.loads(response.content[0].text)
        for pair in pairs:
            qa_pairs.append({
                "instruction": pair["question"],
                "input": "",
                "output": pair["answer"],
                "source": doc.metadata["source_app"]
            })
    
    return qa_pairs

async def main():
    """Main data preparation pipeline."""
    
    # Collect documentation
    docs = await collect_documentation()
    print(f"Collected {len(docs)} documents")
    
    # Generate Q&A pairs
    qa_pairs = await generate_qa_pairs(docs)
    print(f"Generated {len(qa_pairs)} Q&A pairs")
    
    # Save to JSONL
    with open("autoarr_training_data.jsonl", "w") as f:
        for pair in qa_pairs:
            f.write(json.dumps(pair) + "\n")
    
    print("Training data saved to autoarr_training_data.jsonl")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 💾 Infrastructure Requirements

### Training Setup

**Option 1: Personal Workstation**
- **GPU**: RTX 4090 (24GB) or RTX 4080 (16GB)
- **RAM**: 32GB minimum
- **Storage**: 200GB SSD
- **Cost**: $1,500-2,000 (one-time)
- **Training Time**: 2-4 hours per experiment

**Option 2: Budget Server**
- **GPU**: Used Tesla P40 (24GB) ~$400
- **CPU**: Any modern CPU
- **RAM**: 32GB
- **Storage**: 500GB SSD
- **Cost**: $800-1,000 (one-time)
- **Training Time**: 4-6 hours per experiment

**Option 3: Rented GPU (Vast.ai, RunPod)**
- **GPU**: A100 40GB
- **Cost**: $0.50-1.00/hour
- **Training Time**: 1-2 hours
- **Total Cost**: $2-5 per training run

### Deployment Setup

**Minimum (Single User):**
- **CPU**: 4 cores
- **RAM**: 8GB
- **GPU**: Optional (CPU inference possible with quantization)
- **Storage**: 20GB

**Recommended (Production):**
- **CPU**: 8 cores
- **RAM**: 16GB
- **GPU**: RTX 3060 (12GB) or better
- **Storage**: 50GB SSD

---

## 📈 Evaluation Strategy

### Test Set Creation

```python
# Create test set (10% of data)
from sklearn.model_selection import train_test_split

# Load full dataset
with open("autoarr_training_data.jsonl") as f:
    data = [json.loads(line) for line in f]

# Split
train_data, test_data = train_test_split(data, test_size=0.1, random_state=42)

# Save
with open("train.jsonl", "w") as f:
    for item in train_data:
        f.write(json.dumps(item) + "\n")

with open("test.jsonl", "w") as f:
    for item in test_data:
        f.write(json.dumps(item) + "\n")
```

### Evaluation Metrics

```python
# scripts/evaluate_model.py
from transformers import AutoModelForCausalLM, AutoTokenizer
import json
from rouge_score import rouge_scorer
from bert_score import score as bert_score

def evaluate_model(model_path: str, test_file: str):
    """Evaluate model on test set."""
    
    # Load model
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(model_path)
    
    # Load test data
    with open(test_file) as f:
        test_data = [json.loads(line) for line in f]
    
    # Metrics
    rouge = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'])
    
    predictions = []
    references = []
    
    for item in test_data:
        prompt = f"Question: {item['instruction']}\nAnswer:"
        inputs = tokenizer(prompt, return_tensors="pt")
        
        outputs = model.generate(**inputs, max_new_tokens=256)
        prediction = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        predictions.append(prediction)
        references.append(item['output'])
    
    # Calculate ROUGE scores
    rouge_scores = [rouge.score(ref, pred) for ref, pred in zip(references, predictions)]
    
    # Calculate BERTScore
    P, R, F1 = bert_score(predictions, references, lang='en')
    
    print(f"Average ROUGE-L: {sum(s['rougeL'].fmeasure for s in rouge_scores) / len(rouge_scores):.4f}")
    print(f"Average BERTScore F1: {F1.mean():.4f}")
```

---

## 🔄 Continuous Improvement

### Model Update Pipeline

```python
# scripts/update_model.py
"""
Periodic model update pipeline:
1. Collect new documentation
2. Generate new Q&A pairs
3. Fine-tune on new data
4. Evaluate
5. Deploy if improvement
"""

async def update_pipeline():
    """Run complete update pipeline."""
    
    # 1. Collect latest docs
    new_docs = await collect_latest_documentation()
    
    # 2. Generate Q&A pairs
    new_qa = await generate_qa_pairs(new_docs)
    
    # 3. Combine with existing data
    existing_data = load_existing_data()
    combined_data = existing_data + new_qa
    
    # 4. Train new model
    new_model_path = train_lora_model(combined_data)
    
    # 5. Evaluate
    new_score = evaluate_model(new_model_path)
    old_score = evaluate_model(current_model_path)
    
    # 6. Deploy if better
    if new_score > old_score:
        deploy_model(new_model_path)
        print(f"Deployed new model! Score improved: {old_score:.4f} → {new_score:.4f}")
    else:
        print(f"Keeping current model. New score: {new_score:.4f} vs {old_score:.4f}")
```

---

## 💰 Cost Analysis

### One-Time Costs

| Item | Cost |
|------|------|
| RTX 4090 GPU | $1,600 |
| Supporting hardware | $800 |
| **Total** | **$2,400** |

### Operational Costs

| Item | Monthly Cost |
|------|--------------|
| Electricity (~200W 24/7) | $15-20 |
| **Total** | **$15-20/month** |

### Cost Comparison vs. Cloud

**Cloud API (Claude/GPT-4):**
- $15 per 1M input tokens
- Estimated monthly cost: $200-500
- **Annual**: $2,400-6,000

**Local Model:**
- One-time: $2,400
- Annual electricity: $180-240
- **Pays for itself in 3-6 months**

---

## ✅ Implementation Checklist

### Phase 1: Data Collection (Week 1)
- [ ] Set up data collection scripts
- [ ] Scrape *arr documentation
- [ ] Collect community knowledge
- [ ] Generate Q&A pairs with Claude
- [ ] Create train/test split
- **Target**: 10,000+ examples

### Phase 2: Training Setup (Week 2)
- [ ] Set up training environment
- [ ] Install dependencies
- [ ] Configure LoRA training
- [ ] Run first training experiment
- [ ] Evaluate results
- **Target**: Baseline model trained

### Phase 3: Optimization (Week 3-4)
- [ ] Hyperparameter tuning
- [ ] Data quality improvements
- [ ] Additional training rounds
- [ ] Performance evaluation
- **Target**: Production-ready model

### Phase 4: Deployment (Week 5)
- [ ] Convert to GGUF format
- [ ] Set up Ollama
- [ ] Integrate with AutoArr API
- [ ] Create fallback to Claude API
- [ ] Test end-to-end
- **Target**: Model serving locally

### Phase 5: RAG Integration (Week 6)
- [ ] Set up vector database
- [ ] Embed documentation
- [ ] Implement RAG pipeline
- [ ] Add web search capability
- [ ] Test and optimize
- **Target**: Full intelligence system

---

## 📚 Resources

### Documentation
- **Llama Models**: https://github.com/meta-llama/llama-models
- **LoRA Paper**: https://arxiv.org/abs/2106.09685
- **LangChain Docs**: https://python.langchain.com/
- **Ollama**: https://ollama.com/

### Tools
- **Axolotl**: https://github.com/OpenAccess-AI-Collective/axolotl (training framework)
- **Unsloth**: https://github.com/unslothai/unsloth (2x faster training)
- **vLLM**: https://github.com/vllm-project/vllm (fast inference)

### Communities
- **r/LocalLLaMA**: Reddit community for local LLMs
- **Hugging Face Discord**: Active community
- **Ollama Discord**: Deployment help

---

## 🎯 Success Criteria

**Model is ready when:**
- ✅ Answers 90%+ of *arr questions accurately
- ✅ Inference time <2 seconds on target hardware
- ✅ Memory usage <8GB VRAM
- ✅ Better than rule-based system on blind test
- ✅ Can run 24/7 on consumer hardware

---

## 🚀 Quick Start

**Get started today:**

```bash
# 1. Set up environment
conda create -n autoarr-llm python=3.10
conda activate autoarr-llm
pip install -r requirements-llm.txt

# 2. Collect data
python scripts/prepare_training_data.py

# 3. Train model
python scripts/train_lora.py

# 4. Deploy with Ollama
ollama create autoarr -f Modelfile
ollama run autoarr

# 5. Test
curl http://localhost:11434/api/generate -d '{
  "model": "autoarr",
  "prompt": "What is the optimal SABnzbd configuration?"
}'
```

---

*Document Version: 1.0*  
*Last Updated: October 5, 2025*  
*Owner: AutoArr Team*
