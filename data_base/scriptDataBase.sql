-- Criação do banco de dados
CREATE DATABASE IF NOT EXISTS tcc_refatoracao_llm 
CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE tcc_refatoracao_llm;

-- 1. Tabela para os desafios do LeetCode
-- Ajustado: AUTO_INCREMENT adicionado para evitar o erro 1364
CREATE TABLE desafios (
    id_desafio INT AUTO_INCREMENT PRIMARY KEY, 
    titulo VARCHAR(255) NOT NULL,
    enunciado LONGTEXT NOT NULL, -- Alterado para LONGTEXT para suportar enunciados complexos
    nivel ENUM('Easy', 'Medium', 'Hard') NOT NULL
);

-- 2. Tabela para os modelos LLM
CREATE TABLE modelos (
    id_modelo INT AUTO_INCREMENT PRIMARY KEY,
    nome_modelo VARCHAR(100) NOT NULL
);

-- 3. Tabela para as soluções e métricas
CREATE TABLE resultados (
    id_resultado INT AUTO_INCREMENT PRIMARY KEY,
    id_desafio INT,
    id_modelo INT,
    tipo ENUM('baseline', 'refatorado') NOT NULL,
    codigo_fonte MEDIUMTEXT, 
    
    -- Métricas do SonarQube
    code_smells INT DEFAULT 0,
    divida_tecnica INT DEFAULT 0, -- Em minutos
    complexidade_ciclomatica INT DEFAULT 0,
    duplicacao_percentual FLOAT DEFAULT 0.0,
    loc INT DEFAULT 0,
    
    data_geracao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (id_desafio) REFERENCES desafios(id_desafio) ON DELETE CASCADE,
    FOREIGN KEY (id_modelo) REFERENCES modelos(id_modelo) ON DELETE CASCADE
);

-- Inserção inicial dos modelos
INSERT INTO modelos (nome_modelo) VALUES 
('Google Gemini'), 
('GPT-3.5-Turbo'), 
('LLAMA 4'), 
('Gemma 3');