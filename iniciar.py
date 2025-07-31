import sqlite3
import os

# Remove o banco de dados existente se estiver corrompido
if os.path.exists('banco.db'):
    try:
        os.remove('banco.db')
    except Exception as e:
        print(f"Erro ao remover banco corrompido: {e}")

# Cria um novo banco de dados
try:
    conexao = sqlite3.connect('banco.db')
    
    # Ativa chaves estrangeiras
    conexao.execute("PRAGMA foreign_keys = ON")
    
    with open('schema.sql') as f:
        script = f.read()
        # Executa cada comando separadamente
        for comando in script.split(';'):
            if comando.strip():
                conexao.execute(comando)
    
    conexao.commit()
    print("Banco de dados criado com sucesso!")
    
except Exception as e:
    print(f"Erro ao criar banco de dados: {e}")
finally:
    if 'conexao' in locals():
        conexao.close()