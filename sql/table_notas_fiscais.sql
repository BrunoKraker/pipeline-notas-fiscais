CREATE TABLE notas_fiscais (
    id INT IDENTITY PRIMARY KEY,
    chave_acesso VARCHAR(44) UNIQUE NOT NULL,
    numero_nota VARCHAR(20),
    data_emissao DATE,
    cnpj_emitente VARCHAR(14),
    razao_social_emitente VARCHAR(200),
    cnpj_tomador VARCHAR(14),
    razao_social_tomador VARCHAR(200),
    valor_total DECIMAL(15,2)
);

select * from notas_fiscais;