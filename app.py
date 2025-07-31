from flask import Flask, render_template
from flask import request, session, redirect, url_for
from flask import flash

from flask_login import LoginManager, UserMixin, logout_user
from flask_login import login_required, login_user, current_user

from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

import sqlite3

# Criação da aplicação Flask
app = Flask(__name__)
app.secret_key = 'chave_secreta'  # Deve ser uma chave longa e aleatória em produção

# Configuração do Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)  # Correção: usando init_app em vez de __init__
login_manager.login_view = 'login'  # Especifica a rota de login

# Adicione isto após a criação do login_manager (não pode estar dentro de outra função/classe)
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# Configuração do banco de dados
def obter_conexao():
    conn = sqlite3.connect('banco.db')
    conn.row_factory = sqlite3.Row
    return conn

# Modelo de usuário
class User(UserMixin):
    def __init__(self, id, nome, senha):
        self.id = id  # OBRIGATÓRIO para Flask-Login
        self.nome = nome
        self.senha = senha

    @classmethod
    def get(cls, user_id):
        conexao = obter_conexao()        
        sql = "SELECT * FROM users WHERE id = ?"  # Certifique-se que busca por ID
        resultado = conexao.execute(sql, (user_id,)).fetchone()
        conexao.close()
        if resultado:
            return User(id=resultado['id'], nome=resultado['nome'], senha=resultado['senha'])
        return None

# Rotas principais
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/base')
def base():
    return redirect(url_for('index'))

# Rotas de autenticação
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        nome = request.form['name']
        senha = request.form['password']

        conexao = obter_conexao()
        sql = "SELECT * FROM users WHERE nome = ?"
        resultado = conexao.execute(sql, (nome,)).fetchone()
        conexao.close()

        if resultado and check_password_hash(resultado['senha'], senha):
            user = User(id=resultado['id'], nome=resultado['nome'], senha=resultado['senha'])
            login_user(user)
            return redirect(url_for('dash'))
        
        flash('Nome de usuário ou senha incorretos', category='error')
        return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form['name']
        senha = generate_password_hash(request.form['password'])  # Gerar hash aqui

        conexao = obter_conexao()
        try:
            sql = "INSERT INTO users(nome, senha) VALUES(?,?)"
            cursor = conexao.execute(sql, (nome, senha))
            conexao.commit()
            
            user = User(id=cursor.lastrowid, nome=nome, senha=senha)
            login_user(user)
            return redirect(url_for('dash'))
        except sqlite3.IntegrityError:
            flash('Usuário já existe', category='error')
        finally:
            conexao.close()

    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dash():
    return render_template('dash.html')

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Rotas de produtos e carrinho (simplificadas para exemplo)
@app.route('/produtos')
@login_required
def listar_produtos():
    # Exemplo de produtos - você pode substituir por dados do banco
    produtos = [
        {'id': 1, 'nome': 'Produto 1', 'preco': 10.99},
        {'id': 2, 'nome': 'Produto 2', 'preco': 20.50},
        {'id': 3, 'nome': 'Produto 3', 'preco': 15.75}
    ]
    return render_template('produtos.html', produtos=produtos)

@app.route('/add_carrinho/<int:produto_id>')
@login_required
def add_carrinho(produto_id):
    if 'carrinho' not in session:
        session['carrinho'] = []
    
    # Adiciona o produto ao carrinho (simplificado)
    session['carrinho'].append(produto_id)
    session.modified = True
    flash('Produto adicionado ao carrinho', category='success')
    return redirect(url_for('listar_produtos'))

@app.route('/carrinho')
@login_required
def ver_carrinho():
    carrinho = []
    if 'carrinho' in session:
        # Simulação de produtos no carrinho
        produtos = {
            1: {'nome': 'Produto 1', 'preco': 10.99},
            2: {'nome': 'Produto 2', 'preco': 20.50},
            3: {'nome': 'Produto 3', 'preco': 15.75}
        }
        for produto_id in session['carrinho']:
            if produto_id in produtos:
                carrinho.append(produtos[produto_id])
    
    return render_template('carrinho.html', carrinho=carrinho)

@app.route('/limpar_carrinho')
@login_required
def limpar_carrinho():
    if 'carrinho' in session:
        session.pop('carrinho')
    return redirect(url_for('ver_carrinho'))

@app.route('/debug_users')
def debug_users():
    conexao = obter_conexao()
    users = conexao.execute("SELECT * FROM users").fetchall()
    conexao.close()
    return str([dict(user) for user in users])

# Adicione estas rotas após as rotas de autenticação

# Rotas para Festas
@app.route('/festas')
@login_required
def listar_festas():
    conexao = obter_conexao()
    sql = """
    SELECT f.id, f.nome, f.data, f.local 
    FROM festas f
    WHERE f.user_id = ?
    """
    festas = conexao.execute(sql, (current_user.id,)).fetchall()
    conexao.close()
    return render_template('festas.html', festas=festas)

@app.route('/festa/nova', methods=['GET', 'POST'])
@login_required
def nova_festa():
    if request.method == 'POST':
        nome = request.form['nome']
        data = request.form['data']
        local = request.form['local']
        
        conexao = obter_conexao()
        try:
            sql = "INSERT INTO festas (nome, data, local, user_id) VALUES (?, ?, ?, ?)"
            conexao.execute(sql, (nome, data, local, current_user.id))
            conexao.commit()
            flash('Festa cadastrada com sucesso!', 'success')
            return redirect(url_for('listar_festas'))
        except Exception as e:
            flash(f'Erro ao cadastrar festa: {str(e)}', 'error')
        finally:
            conexao.close()
    
    return render_template('nova_festa.html')

@app.route('/festa/remover/<int:festa_id>', methods=['POST'])
@login_required
def remover_festa(festa_id):
    conexao = obter_conexao()
    try:
        sql = "DELETE FROM festas WHERE id = ? AND user_id = ?"
        conexao.execute(sql, (festa_id, current_user.id))
        conexao.commit()
        flash('Festa removida com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao remover festa: {str(e)}', 'error')
    finally:
        conexao.close()
    return redirect(url_for('listar_festas'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)