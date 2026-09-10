# Product Requirement Document (PRD) — LLM Router Gateway

## 1. Visão Geral do Produto
O **LLM Router Gateway** é um microsserviço de alta performance e baixa latência desenvolvido em Python (FastAPI) para orquestrar, rotear e otimizar requisições direcionadas a múltiplos Provedores de Modelos de Linguagem (LLMs). 

O sistema atua como uma fachada única (Proxy/Reverse Gateway) para aplicações internas, interceptando chamadas para aplicar caching inteligente, roteamento por complexidade e resiliência com fallback automático.

---

## 2. Problema de Negócio & Engenharia
1. **Custo Ineficiente:** Enviar prompts simples e repetitivos para modelos de alto custo gera custos computacionais desnecessários.
2. **Latência Elevada:** Depender exclusivamente de APIs externas pode introduzir gargalos de tempo de resposta em operações críticas.
3. **Ponto Único de Falha:** Instabilidade em um único provedor de IA pode derrubar os microsserviços dependentes.

---

## 3. Objetivos Principais
* **Redução de Latência:** Responder requisições repetidas em <10ms via camada de Cache em Redis.
* **Otimização de Custos:** Reduzir o volume de tokens enviados para APIs pagas em pelo menos 30% através do roteamento para modelos locais/menores.
* **Alta Concorrência:** Suportar requisições assíncronas não-bloqueantes com `asyncio` e `httpx`.
* **Observabilidade:** Retornar métricas claras de latência, origem do modelo utilizado e status de cache no cabeçalho ou payload da resposta.

---

## 4. Requisitos Funcionais (RF)

### RF-01: Endpoints da API
* `POST /v1/chat/completions`: Endpoint compatível com a estrutura de payload padrão (mensagens, temperatura, max_tokens).
* `GET /health`: Endpoint para checagem de saúde da API, conexão com Redis e provedores upstream.

### RF-02: Camada de Caching (Redis)
* **Exact Match Cache:** Gerar hash SHA-256 da string do prompt/mensagens e armazenar a resposta com TTL configurável.
* Retornar o campo `cached: true` e `latency_ms` reduzido quando houver cache hit.

### RF-03: Classificação e Roteamento Inteligente
* O sistema deve possuir um serviço de avaliação de complexidade que analisa:
  1. Tamanho do prompt (contagem de palavras/tokens aproximada).
  2. Palavras-chave indicadoras de código, lógica avançada ou raciocínio estruturado.
* **Rota Simples:** Prompts de baixa complexidade são enviados para a instância do modelo local (vLLM / Ollama - ex: Llama 3 8B).
* **Rota Complexa:** Prompts de alta complexidade são enviados para o Provedor Cloud (ex: OpenAI / Anthropic).

### RF-04: Resiliência e Fallback
* Se o Provedor Primário (Local ou Cloud) retornar erro HTTP 5xx ou Timeout, o Gateway deve tentar automaticamente o Provedor Secundário (Fallback) antes de falhar a requisição.

---

## 5. Requisitos Não-Funcionais (RNF)

* **RNF-01 (Performance):** A API deve utilizar padrão totalmente assíncrono em Python (FastAPI + `asyncio` + `httpx` + `redis-py` async).
* **RNF-02 (Validação Estrita):** Uso de Pydantic v2 para validação rigorosa dos esquemas de entrada e saída.
* **RNF-03 (Containerização):** Arquivo `docker-compose.yml` provendo a aplicação FastAPI e a instância do Redis em ambiente isolado.
* **RNF-04 (Qualidade e Testes):** Testes automatizados assíncronos cobrindo os fluxos de roteamento, cache hit/miss e rotas de fallback usando `pytest-asyncio`.

---

## 6. Arquitetura da Solução e Fluxo de Dados

```text
               +-----------------------+
               |  Cliente / Aplicação  |
               +-----------+-----------+
                           |
            POST /v1/chat/completions
                           |
                           v
               +-----------------------+
               |  FastAPI Router (Async)|
               +-----------+-----------+
                           |
             1. Checar Cache SHA-256
                           |
          +----------------+----------------+
          | (Cache Hit)                     | (Cache Miss)
          v                                 v
+------------------+             +-----------------------+
|  Retorna Redis   |             | Evaluator Service     |
|  (Latência <10ms)|             | (Analisa Complexidade)|
+------------------+             +-----------+-----------+
                                             |
                      +----------------------+----------------------+
                      | (Baixa Complexidade)                        | (Alta Complexidade)
                      v                                             v
           +--------------------+                        +--------------------+
           | Provedor Local     |                        | Provedor Cloud     |
           | (Ollama / vLLM)    |                        | (OpenAI / Anthropic|
           +---------+----------+                        +---------+----------+
                     |                                             |
                     +----------------------+----------------------+
                                            |
                                  2. Grava Resposta no Redis
                                            |
                                            v
                                  Retorna Resposta Final
