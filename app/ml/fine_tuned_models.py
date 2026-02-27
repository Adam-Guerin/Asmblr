"""
Custom Fine-Tuned Models for Asmblr
Advanced ML models fine-tuned on domain-specific data for optimal performance
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import torch
import torch.nn as nn
from transformers import (
    AutoTokenizer, AutoModelForCausalLM, 
    AutoModelForSequenceClassification,
    TrainingArguments, Trainer,
    DataCollatorForLanguageModel
)
from datasets import Dataset, load_dataset
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
import redis
import pickle
from concurrent.futures import ThreadPoolExecutor
import os
import gc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FineTuningConfig:
    """Configuration for fine-tuning"""
    model_name: str
    base_model: str
    task_type: str  # "generation", "classification", "embedding"
    training_data_path: str
    validation_split: float = 0.2
    max_length: int = 512
    batch_size: int = 8
    learning_rate: float = 5e-5
    num_epochs: int = 3
    warmup_steps: int = 100
    weight_decay: float = 0.01
    save_steps: int = 500
    eval_steps: int = 500
    logging_steps: int = 100
    output_dir: str = "./models/fine-tuned"


class AsmblrDataset:
    """Dataset for Asmblr-specific fine-tuning"""
    
    def __init__(self, data_path: str, task_type: str):
        self.data_path = Path(data_path)
        self.task_type = task_type
        self.data = self._load_data()
    
    def _load_data(self) -> List[Dict[str, Any]]:
        """Load training data"""
        if self.task_type == "generation":
            return self._load_generation_data()
        elif self.task_type == "classification":
            return self._load_classification_data()
        elif self.task_type == "embedding":
            return self._load_embedding_data()
        else:
            raise ValueError(f"Unsupported task type: {self.task_type}")
    
    def _load_generation_data(self) -> List[Dict[str, Any]]:
        """Load data for text generation tasks"""
        data = []
        
        # Load idea descriptions and evaluations
        if (self.data_path / "ideas.json").exists():
            with open(self.data_path / "ideas.json", 'r') as f:
                ideas = json.load(f)
                
                for idea in ideas:
                    # Create training examples
                    prompt = f"Idea: {idea.get('title', '')}\nDescription: {idea.get('description', '')}\nTopic: {idea.get('topic', '')}"
                    response = f"Evaluation: Confidence={idea.get('confidence_score', 0):.2f}, Market Signal={idea.get('market_signal_score', 0):.2f}, Actionability={idea.get('actionability_score', 0):.2f}"
                    
                    data.append({
                        "input": prompt,
                        "output": response,
                        "text": f"{prompt}\n\n{response}"
                    })
        
        # Load MVP descriptions
        if (self.data_path / "mvps.json").exists():
            with open(self.data_path / "mvps.json", 'r') as f:
                mvps = json.load(f)
                
                for mvp in mvps:
                    prompt = f"MVP for idea: {mvp.get('idea_id', '')}\nFrontend: {mvp.get('frontend_stack', '')}\nBackend: {mvp.get('backend_stack', '')}"
                    response = f"Result: Status={mvp.get('status', '')}, Duration={mvp.get('build_duration', 0):.1f}s, Features={mvp.get('features_implemented', 0)}"
                    
                    data.append({
                        "input": prompt,
                        "output": response,
                        "text": f"{prompt}\n\n{response}"
                    })
        
        # Load market research data
        if (self.data_path / "market_research.json").exists():
            with open(self.data_path / "market_research.json", 'r') as f:
                research = json.load(f)
                
                for item in research:
                    prompt = f"Market Analysis: {item.get('topic', '')}\nSources: {len(item.get('sources', []))}"
                    response = f"Insights: {item.get('insights', '')}\nOpportunities: {len(item.get('opportunities', []))}"
                    
                    data.append({
                        "input": prompt,
                        "output": response,
                        "text": f"{prompt}\n\n{response}"
                    })
        
        return data
    
    def _load_classification_data(self) -> List[Dict[str, Any]]:
        """Load data for classification tasks"""
        data = []
        
        # Load idea evaluations for classification
        if (self.data_path / "ideas.json").exists():
            with open(self.data_path / "ideas.json", 'r') as f:
                ideas = json.load(f)
                
                for idea in ideas:
                    text = f"{idea.get('title', '')} {idea.get('description', '')} {idea.get('topic', '')}"
                    
                    # Multi-label classification
                    labels = []
                    if idea.get('confidence_score', 0) > 0.7:
                        labels.append("high_confidence")
                    if idea.get('market_signal_score', 0) > 0.7:
                        labels.append("strong_market")
                    if idea.get('actionability_score', 0) > 0.7:
                        labels.append("high_actionability")
                    
                    data.append({
                        "text": text,
                        "labels": labels,
                        "confidence": idea.get('confidence_score', 0),
                        "market_signal": idea.get('market_signal_score', 0),
                        "actionability": idea.get('actionability_score', 0)
                    })
        
        return data
    
    def _load_embedding_data(self) -> List[Dict[str, Any]]:
        """Load data for embedding tasks"""
        data = []
        
        # Load all text data for embedding training
        all_texts = []
        
        # Ideas
        if (self.data_path / "ideas.json").exists():
            with open(self.data_path / "ideas.json", 'r') as f:
                ideas = json.load(f)
                for idea in ideas:
                    all_texts.append(f"{idea.get('title', '')} {idea.get('description', '')}")
        
        # MVPs
        if (self.data_path / "mvps.json").exists():
            with open(self.data_path / "mvps.json", 'r') as f:
                mvps = json.load(f)
                for mvp in mvps:
                    all_texts.append(f"{mvp.get('frontend_stack', '')} {mvp.get('backend_stack', '')}")
        
        # Market research
        if (self.data_path / "market_research.json").exists():
            with open(self.data_path / "market_research.json", 'r') as f:
                research = json.load(f)
                for item in research:
                    all_texts.append(item.get('topic', ''))
        
        for text in all_texts:
            data.append({"text": text})
        
        return data
    
    def to_huggingface_dataset(self) -> Dataset:
        """Convert to HuggingFace Dataset"""
        if self.task_type == "generation":
            return Dataset.from_dict({
                "text": [item["text"] for item in self.data]
            })
        elif self.task_type == "classification":
            return Dataset.from_dict({
                "text": [item["text"] for item in self.data],
                "labels": [item["labels"] for item in self.data]
            })
        elif self.task_type == "embedding":
            return Dataset.from_dict({
                "text": [item["text"] for item in self.data]
            })


class CustomModelTrainer:
    """Trainer for custom fine-tuned models"""
    
    def __init__(self, config: FineTuningConfig):
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = None
        self.model = None
        self.trainer = None
        
    async def setup(self) -> None:
        """Setup tokenizer and model"""
        logger.info(f"Setting up model: {self.config.base_model}")
        
        # Initialize tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.base_model,
            trust_remote_code=True
        )
        
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Initialize model based on task type
        if self.config.task_type == "generation":
            self.model = AutoModelForCausalLM.from_pretrained(
                self.config.base_model,
                trust_remote_code=True,
                torch_dtype=torch.float16 if self.device.type == "cuda" else torch.float32
            )
        elif self.config.task_type == "classification":
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.config.base_model,
                trust_remote_code=True,
                num_labels=3  # confidence, market_signal, actionability
            )
        elif self.config.task_type == "embedding":
            self.model = AutoModelForCausalLM.from_pretrained(
                self.config.base_model,
                trust_remote_code=True,
                torch_dtype=torch.float16 if self.device.type == "cuda" else torch.float32
            )
        
        self.model.to(self.device)
        
        logger.info(f"Model setup complete. Device: {self.device}")
    
    async def train(self) -> Dict[str, Any]:
        """Train the model"""
        try:
            # Load dataset
            dataset = AsmblrDataset(self.config.training_data_path, self.config.task_type)
            hf_dataset = dataset.to_huggingface_dataset()
            
            # Split dataset
            if len(hf_dataset) > 1:
                train_test_split = hf_dataset.train_test_split(
                    test_size=self.config.validation_split,
                    seed=42
                )
                train_dataset = train_test_split["train"]
                eval_dataset = train_test_split["test"]
            else:
                train_dataset = hf_dataset
                eval_dataset = None
            
            # Setup training arguments
            training_args = TrainingArguments(
                output_dir=self.config.output_dir,
                num_train_epochs=self.config.num_epochs,
                per_device_train_batch_size=self.config.batch_size,
                per_device_eval_batch_size=self.config.batch_size,
                learning_rate=self.config.learning_rate,
                weight_decay=self.config.weight_decay,
                warmup_steps=self.config.warmup_steps,
                logging_steps=self.config.logging_steps,
                save_steps=self.config.save_steps,
                eval_steps=self.config.eval_steps,
                evaluation_strategy="steps" if eval_dataset else "no",
                load_best_model_at_end=True,
                metric_for_best_model="eval_loss",
                greater_is_better=False,
                fp16=self.device.type == "cuda",
                dataloader_num_workers=2,
                remove_unused_columns=False,
                push_to_hub=False,
            )
            
            # Setup data collator
            if self.config.task_type == "generation":
                data_collator = DataCollatorForLanguageModel(
                    tokenizer=self.tokenizer,
                    mlm=False
                )
            else:
                data_collator = None
            
            # Create trainer
            self.trainer = Trainer(
                model=self.model,
                args=training_args,
                train_dataset=train_dataset,
                eval_dataset=eval_dataset,
                data_collator=data_collator,
                tokenizer=self.tokenizer,
            )
            
            # Start training
            logger.info("Starting model training...")
            train_result = self.trainer.train()
            
            # Save model
            self.trainer.save_model()
            self.tokenizer.save_pretrained(self.config.output_dir)
            
            # Evaluate if we have eval dataset
            eval_results = {}
            if eval_dataset:
                eval_results = self.trainer.evaluate()
            
            logger.info("Training completed successfully")
            
            return {
                "status": "completed",
                "train_loss": train_result.training_loss,
                "eval_results": eval_results,
                "model_path": self.config.output_dir
            }
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def load_model(self, model_path: str) -> None:
        """Load a fine-tuned model"""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.model = AutoModelForCausalLM.from_pretrained(model_path)
            self.model.to(self.device)
            
            logger.info(f"Model loaded from {model_path}")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    async def generate_text(self, prompt: str, max_length: int = 256, 
                           temperature: float = 0.7, top_p: float = 0.9) -> str:
        """Generate text using the fine-tuned model"""
        try:
            if not self.model or not self.tokenizer:
                raise ValueError("Model not loaded")
            
            # Tokenize input
            inputs = self.tokenizer.encode(prompt, return_tensors="pt").to(self.device)
            
            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=max_length,
                    temperature=temperature,
                    top_p=top_p,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Remove the original prompt
            if generated_text.startswith(prompt):
                generated_text = generated_text[len(prompt):].strip()
            
            return generated_text
            
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            return f"Generation failed: {str(e)}"
    
    async def classify_text(self, text: str) -> Dict[str, float]:
        """Classify text using the fine-tuned model"""
        try:
            if not self.model or not self.tokenizer:
                raise ValueError("Model not loaded")
            
            # Tokenize input
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, 
                                   padding=True, max_length=512).to(self.device)
            
            # Get predictions
            with torch.no_grad():
                outputs = self.model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            # Map to labels
            labels = ["confidence", "market_signal", "actionability"]
            scores = predictions[0].cpu().numpy()
            
            return {
                label: float(score) 
                for label, score in zip(labels, scores)
            }
            
        except Exception as e:
            logger.error(f"Text classification failed: {e}")
            return {"error": str(e)}


class ModelRegistry:
    """Registry for managing multiple fine-tuned models"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_client = redis.from_url(redis_url)
        self.models: Dict[str, CustomModelTrainer] = {}
        self.model_configs: Dict[str, FineTuningConfig] = {}
        
    async def register_model(self, model_name: str, config: FineTuningConfig) -> None:
        """Register a new model configuration"""
        self.model_configs[model_name] = config
        
        # Save config to Redis
        config_data = {
            "model_name": config.model_name,
            "base_model": config.base_model,
            "task_type": config.task_type,
            "training_data_path": config.training_data_path,
            "max_length": config.max_length,
            "batch_size": config.batch_size,
            "learning_rate": config.learning_rate,
            "num_epochs": config.num_epochs,
            "output_dir": config.output_dir
        }
        
        self.redis_client.hset(
            f"model_config:{model_name}",
            mapping=config_data
        )
        
        logger.info(f"Registered model: {model_name}")
    
    async def train_model(self, model_name: str) -> Dict[str, Any]:
        """Train a registered model"""
        if model_name not in self.model_configs:
            raise ValueError(f"Model {model_name} not registered")
        
        config = self.model_configs[model_name]
        trainer = CustomModelTrainer(config)
        
        # Setup and train
        await trainer.setup()
        result = await trainer.train()
        
        # Store the trained model
        if result["status"] == "completed":
            self.models[model_name] = trainer
            
            # Update Redis with model status
            self.redis_client.hset(
                f"model_status:{model_name}",
                mapping={
                    "status": "trained",
                    "trained_at": datetime.utcnow().isoformat(),
                    "model_path": result["model_path"]
                }
            )
        
        return result
    
    async def load_model(self, model_name: str, model_path: str) -> None:
        """Load a pre-trained model"""
        if model_name not in self.model_configs:
            raise ValueError(f"Model {model_name} not registered")
        
        config = self.model_configs[model_name]
        trainer = CustomModelTrainer(config)
        
        await trainer.load_model(model_path)
        self.models[model_name] = trainer
        
        # Update Redis
        self.redis_client.hset(
            f"model_status:{model_name}",
            mapping={
                "status": "loaded",
                "loaded_at": datetime.utcnow().isoformat(),
                "model_path": model_path
            }
        )
        
        logger.info(f"Loaded model: {model_name}")
    
    async def get_model(self, model_name: str) -> Optional[CustomModelTrainer]:
        """Get a trained model"""
        return self.models.get(model_name)
    
    async def list_models(self) -> Dict[str, Dict[str, Any]]:
        """List all registered models"""
        models = {}
        
        # Get from Redis
        pattern = "model_config:*"
        keys = self.redis_client.keys(pattern)
        
        for key in keys:
            model_name = key.decode().split(":")[1]
            config_data = self.redis_client.hgetall(key)
            
            # Get status
            status_key = f"model_status:{model_name}"
            status_data = self.redis_client.hgetall(status_key)
            
            models[model_name] = {
                "config": {k.decode(): v.decode() for k, v in config_data.items()},
                "status": {k.decode(): v.decode() for k, v in status_data.items()},
                "loaded": model_name in self.models
            }
        
        return models
    
    async def generate_text(self, model_name: str, prompt: str, **kwargs) -> str:
        """Generate text using a specific model"""
        model = await self.get_model(model_name)
        if not model:
            raise ValueError(f"Model {model_name} not available")
        
        return await model.generate_text(prompt, **kwargs)
    
    async def classify_text(self, model_name: str, text: str) -> Dict[str, float]:
        """Classify text using a specific model"""
        model = await self.get_model(model_name)
        if not model:
            raise ValueError(f"Model {model_name} not available")
        
        return await model.classify_text(text)


class ModelManager:
    """High-level manager for fine-tuned models"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.registry = ModelRegistry(redis_url)
        self.default_models = {
            "idea_generator": FineTuningConfig(
                model_name="idea_generator",
                base_model="microsoft/DialoGPT-medium",
                task_type="generation",
                training_data_path="./data/training/ideas",
                max_length=512,
                batch_size=4,
                learning_rate=5e-5,
                num_epochs=3,
                output_dir="./models/fine-tuned/idea_generator"
            ),
            "idea_classifier": FineTuningConfig(
                model_name="idea_classifier",
                base_model="distilbert-base-uncased",
                task_type="classification",
                training_data_path="./data/training/ideas",
                max_length=512,
                batch_size=8,
                learning_rate=3e-5,
                num_epochs=5,
                output_dir="./models/fine-tuned/idea_classifier"
            ),
            "mvp_generator": FineTuningConfig(
                model_name="mvp_generator",
                base_model="microsoft/DialoGPT-small",
                task_type="generation",
                training_data_path="./data/training/mvps",
                max_length=256,
                batch_size=4,
                learning_rate=5e-5,
                num_epochs=3,
                output_dir="./models/fine-tuned/mvp_generator"
            )
        }
    
    async def initialize(self) -> None:
        """Initialize default models"""
        for model_name, config in self.default_models.items():
            await self.registry.register_model(model_name, config)
        
        logger.info("Model manager initialized with default models")
    
    async def train_all_models(self) -> Dict[str, Dict[str, Any]]:
        """Train all registered models"""
        results = {}
        
        for model_name in self.default_models.keys():
            try:
                logger.info(f"Training model: {model_name}")
                result = await self.registry.train_model(model_name)
                results[model_name] = result
                
                # Clear GPU memory after training
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    gc.collect()
                
            except Exception as e:
                logger.error(f"Failed to train {model_name}: {e}")
                results[model_name] = {"status": "failed", "error": str(e)}
        
        return results
    
    async def generate_idea(self, prompt: str, **kwargs) -> str:
        """Generate idea using fine-tuned model"""
        return await self.registry.generate_text("idea_generator", prompt, **kwargs)
    
    async def classify_idea(self, text: str) -> Dict[str, float]:
        """Classify idea using fine-tuned model"""
        return await self.registry.classify_text("idea_classifier", text)
    
    async def generate_mvp_description(self, prompt: str, **kwargs) -> str:
        """Generate MVP description using fine-tuned model"""
        return await self.registry.generate_text("mvp_generator", prompt, **kwargs)
    
    async def get_model_status(self) -> Dict[str, Any]:
        """Get status of all models"""
        return await self.registry.list_models()


# Example usage
async def example_usage():
    """Example of fine-tuned models usage"""
    
    # Initialize model manager
    manager = ModelManager()
    await manager.initialize()
    
    # Train models (this would take time)
    # results = await manager.train_all_models()
    # print(f"Training results: {results}")
    
    # For demonstration, assume models are already trained
    try:
        # Generate an idea
        idea_prompt = "Create a startup idea for sustainable agriculture"
        generated_idea = await manager.generate_idea(idea_prompt, max_length=200)
        print(f"Generated idea: {generated_idea}")
        
        # Classify an idea
        classification = await manager.classify_idea(
            "AI-powered vertical farming platform for urban areas"
        )
        print(f"Idea classification: {classification}")
        
        # Generate MVP description
        mvp_prompt = "MVP for a sustainable agriculture startup"
        mvp_description = await manager.generate_mvp_description(mvp_prompt, max_length=150)
        print(f"MVP description: {mvp_description}")
        
        # Get model status
        status = await manager.get_model_status()
        print(f"Model status: {status}")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(example_usage())
