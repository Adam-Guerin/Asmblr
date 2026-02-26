"""
Tests unitaires pour le module core.llm
Couvre le client LLM, la gestion des modèles et les appels API
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
import httpx

from app.core.llm import LLMClient, LLMResponse


class TestLLMClient:
    """Tests complets pour la classe LLMClient"""

    @pytest.fixture
    def client(self):
        """Fixture pour le client LLM de test"""
        return LLMClient("http://localhost:11434", "llama3.1:8b")

    def test_client_initialization(self):
        """Test l'initialisation du client"""
        base_url = "http://localhost:11434"
        model = "llama3.1:8b"
        
        client = LLMClient(base_url, model)
        
        assert client.base_url == base_url
        assert client.model == model
        assert client.timeout == 30
        assert client.max_retries == 3

    def test_client_initialization_with_options(self):
        """Test l'initialisation avec options personnalisées"""
        client = LLMClient(
            base_url="http://custom:11434",
            model="custom_model",
            timeout=60,
            max_retries=5
        )
        
        assert client.base_url == "http://custom:11434"
        assert client.model == "custom_model"
        assert client.timeout == 60
        assert client.max_retries == 5

    @pytest.mark.asyncio
    async def test_available_success(self, client):
        """Test la vérification de disponibilité réussie"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": [{"name": "llama3.1:8b"}]}
        
        with patch('httpx.AsyncClient.get', return_value=mock_response):
            result = await client.available()
            assert result is True

    @pytest.mark.asyncio
    async def test_available_connection_error(self, client):
        """Test la gestion d'erreur de connexion"""
        with patch('httpx.AsyncClient.get', side_effect=httpx.ConnectError("Connection failed")):
            result = await client.available()
            assert result is False

    @pytest.mark.asyncio
    async def test_available_model_not_found(self, client):
        """Test quand le modèle n'est pas trouvé"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": [{"name": "other_model"}]}
        
        with patch('httpx.AsyncClient.get', return_value=mock_response):
            result = await client.available()
            assert result is False

    @pytest.mark.asyncio
    async def test_generate_success(self, client):
        """Test la génération réussie"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Generated text",
            "done": True,
            "total_duration": 1000
        }
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            response = await client.generate("Test prompt")
            
            assert isinstance(response, LLMResponse)
            assert response.text == "Generated text"
            assert response.done is True
            assert response.total_duration == 1000

    @pytest.mark.asyncio
    async def test_generate_with_options(self, client):
        """Test la génération avec options personnalisées"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Generated text",
            "done": True
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value = mock_response
            await client.generate(
                "Test prompt",
                temperature=0.5,
                max_tokens=100,
                stream=False
            )
            
            # Vérification que les options ont été passées
            call_args = mock_post.call_args
            request_data = json.loads(call_args[1]["content"])
            assert request_data["options"]["temperature"] == 0.5
            assert request_data["options"]["num_predict"] == 100

    @pytest.mark.asyncio
    async def test_generate_api_error(self, client):
        """Test la gestion d'erreur API"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            with pytest.raises(Exception, match="API error"):
                await client.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_with_retry(self, client):
        """Test la logique de retry"""
        # Premier appel échoue, deuxième réussit
        responses = [
            Mock(status_code=500, text="First error"),
            Mock(status_code=200, json=Mock(return_value={"response": "Success", "done": True}))
        ]
        
        with patch('httpx.AsyncClient.post', side_effect=responses):
            response = await client.generate("Test prompt")
            assert response.text == "Success"

    @pytest.mark.asyncio
    async def test_generate_max_retries_exceeded(self, client):
        """Test l'échec après max retries"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Persistent error"
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            with pytest.raises(Exception, match="API error"):
                await client.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_stream(self, client):
        """Test la génération en streaming"""
        # Simulation de streaming
        chunks = [
            '{"response": "Hello", "done": false}',
            '{"response": " world", "done": false}',
            '{"response": "!", "done": true}'
        ]
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.aiter_bytes.return_value = [
            chunk.encode() for chunk in chunks
        ]
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            responses = []
            async for response in client.generate_stream("Test prompt"):
                responses.append(response)
            
            assert len(responses) == 3
            assert responses[0].text == "Hello"
            assert responses[1].text == " world"
            assert responses[2].text == "!"
            assert responses[2].done is True

    @pytest.mark.asyncio
    async def test_list_models(self, client):
        """Test la liste des modèles disponibles"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "llama3.1:8b", "size": 8000000000},
                {"name": "qwen2.5:7b", "size": 7000000000}
            ]
        }
        
        with patch('httpx.AsyncClient.get', return_value=mock_response):
            models = await client.list_models()
            
            assert len(models) == 2
            assert models[0]["name"] == "llama3.1:8b"
            assert models[1]["name"] == "qwen2.5:7b"

    @pytest.mark.asyncio
    async def test_pull_model(self, client):
        """Test le téléchargement d'un modèle"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "pulling model"}
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            result = await client.pull_model("new_model")
            assert result["status"] == "pulling model"

    @pytest.mark.asyncio
    async def test_delete_model(self, client):
        """Test la suppression d'un modèle"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "deleted"}
        
        with patch('httpx.AsyncClient.delete', return_value=mock_response):
            result = await client.delete_model("old_model")
            assert result["status"] == "deleted"

    def test_build_request_data(self, client):
        """Test la construction des données de requête"""
        prompt = "Test prompt"
        options = {
            "temperature": 0.7,
            "max_tokens": 150,
            "top_p": 0.9
        }
        
        data = client._build_request_data(prompt, **options)
        
        assert data["model"] == client.model
        assert data["prompt"] == prompt
        assert data["options"]["temperature"] == 0.7
        assert data["options"]["num_predict"] == 150
        assert data["options"]["top_p"] == 0.9

    def test_parse_response(self, client):
        """Test le parsing de la réponse API"""
        api_response = {
            "response": "Generated text",
            "done": True,
            "total_duration": 1500,
            "load_duration": 100,
            "prompt_eval_count": 10,
            "eval_count": 20
        }
        
        response = client._parse_response(api_response)
        
        assert isinstance(response, LLMResponse)
        assert response.text == "Generated text"
        assert response.done is True
        assert response.total_duration == 1500
        assert response.load_duration == 100
        assert response.prompt_eval_count == 10
        assert response.eval_count == 20

    def test_parse_stream_chunk(self, client):
        """Test le parsing d'un chunk de streaming"""
        chunk_data = '{"response": "Partial text", "done": false}'
        
        response = client._parse_stream_chunk(chunk_data)
        
        assert isinstance(response, LLMResponse)
        assert response.text == "Partial text"
        assert response.done is False

    def test_is_model_available_true(self, client):
        """Test la vérification de disponibilité d'un modèle (positif)"""
        models = [
            {"name": "llama3.1:8b"},
            {"name": "qwen2.5:7b"}
        ]
        
        result = client._is_model_available(models, "llama3.1:8b")
        assert result is True

    def test_is_model_available_false(self, client):
        """Test la vérification de disponibilité d'un modèle (négatif)"""
        models = [
            {"name": "llama3.1:8b"},
            {"name": "qwen2.5:7b"}
        ]
        
        result = client._is_model_available(models, "nonexistent_model")
        assert result is False

    def test_context_window_info(self, client):
        """Test les informations sur la fenêtre de contexte"""
        info = client.get_context_window_info()
        
        assert "max_tokens" in info
        assert "recommended_max" in info
        assert info["max_tokens"] > 0
        assert info["recommended_max"] < info["max_tokens"]

    def test_estimate_tokens(self, client):
        """Test l'estimation du nombre de tokens"""
        text = "This is a test text for token estimation."
        
        token_count = client.estimate_tokens(text)
        
        assert isinstance(token_count, int)
        assert token_count > 0
        # Estimation approximative: ~4 caractères par token
        expected_approx = len(text) // 4
        assert abs(token_count - expected_approx) < expected_approx * 0.5

    def test_truncate_to_token_limit(self, client):
        """Test la troncation à la limite de tokens"""
        long_text = "word " * 1000  # Texte long
        
        truncated = client.truncate_to_token_limit(long_text, max_tokens=100)
        
        assert len(truncated) < len(long_text)
        estimated_tokens = client.estimate_tokens(truncated)
        assert estimated_tokens <= 100

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, client):
        """Test les requêtes concurrentes"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Response",
            "done": True
        }
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            # Exécution concurrente de plusieurs requêtes
            tasks = [
                client.generate(f"Prompt {i}")
                for i in range(5)
            ]
            responses = await asyncio.gather(*tasks)
            
            assert len(responses) == 5
            assert all(isinstance(r, LLMResponse) for r in responses)

    def test_client_repr(self, client):
        """Test la représentation textuelle du client"""
        repr_str = repr(client)
        
        assert "LLMClient" in repr_str
        assert client.base_url in repr_str
        assert client.model in repr_str
