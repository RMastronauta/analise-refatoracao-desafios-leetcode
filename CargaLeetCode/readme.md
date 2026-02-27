# 📚 Documentação Técnica do Sistema de Carga

Este documento detalha o funcionamento interno do script `carga_leetcode.py`, desenvolvido para a coleta de dados do Trabalho de Conclusão de Curso.

## 1. Visão Geral

O script atua como um pipeline de ETL (Extract, Transform, Load) que extrai desafios de lógica da plataforma LeetCode, realiza o processamento para categorização e persiste as informações em um banco de dados relacional MySQL.

---

## 2. Fluxo de Execução

### A. Autenticação e Configuração

O sistema utiliza a biblioteca `python-dotenv` para carregar as credenciais do banco de dados a partir de um arquivo externo `.env`. Isso garante a segurança e a portabilidade entre diferentes ambientes de desenvolvimento (ex: Máquina Local vs Servidor de Testes).

### B. Coleta da Lista de Desafios (Extração)

Diferente das consultas tradicionais via GraphQL, o script utiliza o endpoint REST público:
`https://leetcode.com/api/problems/all/`

**Motivação técnica:** Este endpoint é menos restritivo e retorna o catálogo completo em um único objeto JSON, reduzindo a complexidade de autenticação e o risco de erros de protocolo (como o erro 400).

### C. Processamento e Filtro (Transformação)

O script percorre a lista bruta e organiza os dados em três estruturas distintas (Easy, Medium, Hard).

- **Critério de Seleção:** Os 100 desafios mais recentes de cada nível que não possuem restrição de pagamento (`paid_only = false`).
- **Mapeamento de Dificuldade:** A API do LeetCode utiliza inteiros (1, 2, 3) que são convertidos para as strings amigáveis utilizadas no TCC.

### D. Extração de Enunciados via GraphQL

Para cada desafio filtrado, o script realiza uma nova requisição ao endpoint `/graphql`.

- **Query utilizada:** `questionContent`.
- **Parâmetro:** `titleSlug`.
- **Tratamento de HTML:** Os enunciados são mantidos em formato HTML para preservar a formatação original (tabelas, blocos de código e fórmulas) para posterior análise das LLMs.

### E. Persistência (Carga)

Os dados são inseridos na tabela `desafios` através da biblioteca `mysql-connector-python`.

- **Modo de Inserção:** Atômica por registro com `commit` em lote a cada 10 registros para garantir performance e integridade.
- **Segurança de Fluxo:** Utiliza um `time.sleep(0.6)` entre cada requisição para evitar que o IP seja bloqueado por _Rate Limiting_.

---

## 3. Funções Principais

| Função                         | Responsabilidade                                                   |
| :----------------------------- | :----------------------------------------------------------------- |
| `get_problems_by_difficulty()` | Conecta à API REST e filtra o top 100 de cada categoria.           |
| `get_description(title_slug)`  | Realiza a consulta GraphQL para obter o texto completo do desafio. |
| `save_to_db(problems)`         | Gerencia a conexão MySQL e executa as instruções INSERT.           |

---

## 4. Dicionário de Dados do Banco

| Campo        | Tipo     | Descrição                                            |
| :----------- | :------- | :--------------------------------------------------- |
| `id_desafio` | INT (PK) | Identificador único autogerado pelo banco.           |
| `titulo`     | VARCHAR  | Nome original do desafio no LeetCode.                |
| `enunciado`  | LONGTEXT | Texto completo do desafio incluindo tags HTML.       |
| `nivel`      | ENUM     | Categoria de dificuldade ('Easy', 'Medium', 'Hard'). |

---

## 5. Considerações Técnicas de Pesquisa

Para fins de reprodutibilidade acadêmica, é importante notar que o script captura o "estado atual" do LeetCode. Como novos desafios são adicionados semanalmente, execuções em datas diferentes podem resultar em bases de dados distintas.

## 6. Instalação e Configuração do Ambiente

Para rodar este projeto, é necessário instalar o motor do Python e as bibliotecas que fazem a ponte entre o script, a web e o banco de dados.

### 6.1. Instalação de Dependências (Terminal)

Execute os seguintes comandos no terminal do VS Code para instalar os pacotes necessários:

```powershell
# Atualiza o gerenciador de pacotes
python -m pip install --upgrade pip

# Instala as bibliotecas do projeto
pip install requests mysql-connector-python python-dotenv

pip install mysql-connector-python tenacity google-generativeai openai

### 6.2. Criando o arquivo .env

O projeto carrega credenciais e configurações a partir de um arquivo `.env` (usando `python-dotenv`). Crie um arquivo chamado `.env` na raiz do projeto (mesmo diretório de `carga_leetcode.py`) e defina as variáveis necessárias. Exemplo mínimo:

```

# Exemplo de .env

MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=nome_do_banco
MYSQL_USER=usuario
MYSQL_PASSWORD=senha
API_KEY=seu_api_key_aqui

```

Como criar o arquivo (exemplos):

- PowerShell:
```

Set-Content -Path .env -Value "MYSQL_HOST=localhost`nMYSQL_PORT=3306`nMYSQL_DATABASE=nome_do_banco`nMYSQL_USER=usuario`nMYSQL_PASSWORD=senha`nAPI_KEY=seu_api_key_aqui"

```

- Bash / WSL / Git Bash:
```

cat > .env << 'EOF'
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=nome_do_banco
MYSQL_USER=usuario
MYSQL_PASSWORD=senha
API_KEY=seu_api_key_aqui
EOF

```

- Manual: abra um editor, cole o conteúdo de exemplo e salve como `.env`.

Segurança e controle de versão:
- Nunca commite o arquivo `.env` no repositório. Para garantir isso, adicione `.env` ao seu `.gitignore`:
```

echo ".env" >> .gitignore

```

Uso no código:
O `python-dotenv` carrega as variáveis de ambiente quando o script chama `load_dotenv()` (verifique se o projeto já faz essa chamada). As variáveis ficam disponíveis via `os.environ` ou `os.getenv()`.
```
