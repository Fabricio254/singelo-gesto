import streamlit as st
from datetime import datetime
from supabase import create_client, Client
import pandas as pd
from PIL import Image

# ==================== CONFIGURAÇÕES ====================
# Configurações do Supabase
# Em produção (Streamlit Cloud), usa secrets
# Em desenvolvimento local, usa as variáveis diretas
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    # Fallback para desenvolvimento local
    SUPABASE_URL = "https://fjgugglxqyhlyxwzvdts.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZqZ3VnZ2x4cXlobHl4d3p2ZHRzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjAzODI4NzQsImV4cCI6MjA3NTk1ODg3NH0.YGQIfxghu4yK58iVoklI1YkwwH6aoprZ06LUsWzcYPk"

# Inicializar Supabase
@st.cache_resource
def init_supabase():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"Erro ao conectar: {str(e)}")
        return None

# ==================== ESTILO E CORES ====================
def apply_custom_style():
    st.markdown("""
        <style>
        /* Cores baseadas na logo Singelo Gesto */
        :root {
            --primary-color: #C9A58A;
            --secondary-color: #A67C6B;
            --background-color: #F5E6DC;
            --text-color: #6B4E3D;
        }
        
        .stApp {
            background-color: #F5E6DC;
        }
        
        .main-header {
            text-align: center;
            color: #A67C6B;
            font-family: 'Serif';
            padding: 20px 0;
            border-bottom: 2px solid #C9A58A;
            margin-bottom: 30px;
        }
        
        .logo-container {
            display: flex;
            justify-content: center;
            margin-bottom: 20px;
        }
        
        .box-card {
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            border: 2px solid #C9A58A;
            margin: 10px 0;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        .stButton>button {
            background-color: #A67C6B;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 10px 25px;
            font-weight: bold;
            width: 100%;
        }
        
        .stButton>button:hover {
            background-color: #8B6353;
        }
        
        .success-message {
            background-color: #D4EDDA;
            color: #155724;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #28A745;
            margin: 10px 0;
        }
        
        .metric-card {
            background: linear-gradient(135deg, #C9A58A 0%, #A67C6B 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            margin: 10px 0;
        }
        
        h1, h2, h3 {
            color: #A67C6B;
        }
        
        .stSelectbox label, .stNumberInput label, .stTextInput label {
            color: #6B4E3D !important;
            font-weight: 600;
        }
        </style>
    """, unsafe_allow_html=True)

# ==================== BOXES PREDEFINIDAS ====================
BOXES = [
    "Box Café da manhã/tarde",
    "Box Chocolate",
    "Box Maternidade",
    "Box Casamento",
    "Box Aniversário",
    "Box Formatura"
]

# ==================== TAMANHOS E CUSTOS ====================
TAMANHOS = {
    "Box mini": 20.00,
    "Box PP": 30.00,
    "Box P": 40.00,
    "Box M": 50.00,
    "Box master": 60.00
}

# ==================== FUNÇÕES DO BANCO DE DADOS ====================
def criar_tabelas():
    """Cria as tabelas no Supabase se não existirem"""
    # Nota: As tabelas devem ser criadas no Supabase Dashboard
    # Esta função é apenas informativa
    st.info("""
    🔧 **Tabelas necessárias no Supabase:**
    
    ⚠️ **IMPORTANTE:** Tabelas com prefixo "singelo_" para não conflitar com o sistema existente
    
    **Tabela: singelo_compras**
    - id (int8, primary key, auto-increment)
    - data (timestamp with time zone)
    - valor_total (numeric)
    - descricao (text, opcional)
    - created_at (timestamp with time zone, default now())
    
    **Tabela: singelo_vendas**
    - id (int8, primary key, auto-increment)
    - data (timestamp with time zone)
    - produto (text)
    - quantidade (int4)
    - valor_total (numeric)
    - created_at (timestamp with time zone, default now())
    
    📝 Execute o script SQL fornecido no arquivo 'criar_tabelas.sql'
    """)

def inserir_compra(supabase: Client, valor_total: float, descricao: str = ""):
    """Insere uma nova compra no banco"""
    data = {
        "data": datetime.now().isoformat(),
        "valor_total": valor_total,
        "descricao": descricao
    }
    result = supabase.table("singelo_compras").insert(data).execute()
    return result

def inserir_venda(supabase: Client, produto: str, quantidade: int, valor_total: float, taxa_entrega: float = 0, tamanho: str = ""):
    """Insere uma nova venda no banco"""
    data = {
        "data": datetime.now().isoformat(),
        "produto": produto,
        "quantidade": quantidade,
        "valor_total": valor_total,
        "taxa_entrega": taxa_entrega,
        "tamanho": tamanho
    }
    result = supabase.table("singelo_vendas").insert(data).execute()
    return result

def inserir_entrega(supabase: Client, custo_entregador: float, descricao: str = ""):
    """Insere um custo de entregador no banco"""
    data = {
        "data": datetime.now().isoformat(),
        "custo_entregador": custo_entregador,
        "descricao": descricao
    }
    result = supabase.table("singelo_entregas").insert(data).execute()
    return result

def buscar_entregas(supabase: Client, limite: int = 50):
    """Busca os últimos custos de entrega"""
    result = supabase.table("singelo_entregas").select("*").order("data", desc=True).limit(limite).execute()
    return result.data

def excluir_compra(supabase: Client, compra_id: int):
    """Exclui uma compra do banco"""
    result = supabase.table("singelo_compras").delete().eq("id", compra_id).execute()
    return result

def excluir_venda(supabase: Client, venda_id: int):
    """Exclui uma venda do banco"""
    result = supabase.table("singelo_vendas").delete().eq("id", venda_id).execute()
    return result

def excluir_entrega(supabase: Client, entrega_id: int):
    """Exclui um custo de entrega do banco"""
    result = supabase.table("singelo_entregas").delete().eq("id", entrega_id).execute()
    return result

def buscar_compras(supabase: Client, limite: int = 50):
    """Busca as últimas compras"""
    result = supabase.table("singelo_compras").select("*").order("data", desc=True).limit(limite).execute()
    return result.data

def buscar_vendas(supabase: Client, limite: int = 50):
    """Busca as últimas vendas"""
    result = supabase.table("singelo_vendas").select("*").order("data", desc=True).limit(limite).execute()
    return result.data

def buscar_entregas(supabase: Client, limite: int = 50):
    """Busca os últimos custos de entrega"""
    result = supabase.table("singelo_entregas").select("*").order("data", desc=True).limit(limite).execute()
    return result.data

def calcular_resumo(supabase: Client):
    """Calcula o resumo financeiro"""
    try:
        compras = supabase.table("singelo_compras").select("valor_total").execute()
        vendas = supabase.table("singelo_vendas").select("valor_total, taxa_entrega").execute()
        entregas = supabase.table("singelo_entregas").select("custo_entregador").execute()
        
        total_compras = sum([float(c['valor_total']) for c in compras.data]) if compras.data else 0
        total_vendas = sum([float(v['valor_total']) for v in vendas.data]) if vendas.data else 0
        total_taxa_entrega_cobrada = sum([float(v.get('taxa_entrega', 0)) for v in vendas.data]) if vendas.data else 0
        total_custo_entregador = sum([float(e['custo_entregador']) for e in entregas.data]) if entregas.data else 0
        
        lucro_entregas = total_taxa_entrega_cobrada - total_custo_entregador
        lucro = total_vendas - total_compras
        
        return {
            "total_compras": total_compras,
            "total_vendas": total_vendas,
            "total_taxa_entrega_cobrada": total_taxa_entrega_cobrada,
            "total_custo_entregador": total_custo_entregador,
            "lucro_entregas": lucro_entregas,
            "lucro": lucro
        }
    except Exception as e:
        return {
            "total_compras": 0,
            "total_vendas": 0,
            "total_taxa_entrega_cobrada": 0,
            "total_custo_entregador": 0,
            "lucro_entregas": 0,
            "lucro": 0
        }

# ==================== INTERFACE PRINCIPAL ====================
def main():
    # Configurações da página
    st.set_page_config(
        page_title="Singelo Gesto - Gestão de Vendas",
        page_icon="🎁",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    apply_custom_style()
    
    # Header com logo
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try:
            logo = Image.open("Z:/codigos/Singelo/logo.png")
            st.image(logo, use_container_width=True)
        except:
            st.markdown("<div class='main-header'><h1>🎁 Singelo Gesto</h1><p>Box de Luxo Personalizadas</p></div>", unsafe_allow_html=True)
    
    # Verificar configuração do Supabase
    if "COLE_SUA" in SUPABASE_KEY or SUPABASE_KEY == "SUA_KEY_AQUI":
        st.error("⚠️ **Configure a ANON KEY do Supabase no arquivo app.py**")
        st.info("📝 Cole a sua Anon Key na variável SUPABASE_KEY no início do arquivo app.py")
        criar_tabelas()
        return
    
    # Inicializar Supabase
    try:
        supabase = init_supabase()
    except Exception as e:
        st.error(f"❌ Erro ao conectar com Supabase: {str(e)}")
        return
    
    # Sidebar - Menu
    with st.sidebar:
        st.markdown("### 📊 Menu Principal")
        opcao = st.radio(
            "Selecione uma opção:",
            ["📈 Dashboard", "🛒 Lançar Compra", "💰 Lançar Venda", "🚚 Custo Entregador", "📋 Histórico"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.markdown("### ℹ️ Sobre")
        st.markdown("Sistema de gestão para **Singelo Gesto**")
        st.markdown("Box de Luxo Personalizadas")
    
    # ==================== DASHBOARD ====================
    if opcao == "📈 Dashboard":
        st.markdown("## 📈 Dashboard Financeiro")
        
        resumo = calcular_resumo(supabase)
        
        # Linha 1: Vendas e Compras
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
                <div class='metric-card'>
                    <h3>🛒 Total Compras</h3>
                    <h2>R$ {resumo['total_compras']:,.2f}</h2>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
                <div class='metric-card'>
                    <h3>💰 Total Vendas</h3>
                    <h2>R$ {resumo['total_vendas']:,.2f}</h2>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            lucro_color = "#28A745" if resumo['lucro'] >= 0 else "#DC3545"
            st.markdown(f"""
                <div class='metric-card' style='background: {lucro_color};'>
                    <h3>📊 Lucro Vendas</h3>
                    <h2>R$ {resumo['lucro']:,.2f}</h2>
                </div>
            """, unsafe_allow_html=True)
        
        # Linha 2: Entregas
        st.markdown("### 🚚 Controle de Entregas")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
                <div class='metric-card' style='background: linear-gradient(135deg, #4A90E2 0%, #357ABD 100%);'>
                    <h3>💵 Taxa Cobrada</h3>
                    <h2>R$ {resumo['total_taxa_entrega_cobrada']:,.2f}</h2>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
                <div class='metric-card' style='background: linear-gradient(135deg, #E67E22 0%, #D35400 100%);'>
                    <h3>🚚 Custo Entregador</h3>
                    <h2>R$ {resumo['total_custo_entregador']:,.2f}</h2>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            lucro_entrega_color = "#28A745" if resumo['lucro_entregas'] >= 0 else "#DC3545"
            status_entrega = "Lucro" if resumo['lucro_entregas'] >= 0 else "Prejuízo"
            st.markdown(f"""
                <div class='metric-card' style='background: {lucro_entrega_color};'>
                    <h3>📊 {status_entrega} Entregas</h3>
                    <h2>R$ {resumo['lucro_entregas']:,.2f}</h2>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Últimas movimentações
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🛒 Últimas Compras")
            compras = buscar_compras(supabase, 5)
            if compras:
                for compra in compras:
                    data_formatada = datetime.fromisoformat(compra['data'].replace('Z', '+00:00')).strftime('%d/%m/%Y %H:%M')
                    st.markdown(f"""
                        <div class='box-card'>
                            <strong>📅 {data_formatada}</strong><br>
                            💵 R$ {float(compra['valor_total']):,.2f}<br>
                            {f"📝 {compra.get('descricao', '')}" if compra.get('descricao') else ""}
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Nenhuma compra registrada ainda")
        
        with col2:
            st.markdown("### 💰 Últimas Vendas")
            vendas = buscar_vendas(supabase, 5)
            if vendas:
                for venda in vendas:
                    data_formatada = datetime.fromisoformat(venda['data'].replace('Z', '+00:00')).strftime('%d/%m/%Y %H:%M')
                    st.markdown(f"""
                        <div class='box-card'>
                            <strong>📅 {data_formatada}</strong><br>
                            🎁 {venda['produto']}<br>
                            📦 Quantidade: {venda['quantidade']}<br>
                            💵 R$ {float(venda['valor_total']):,.2f}
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Nenhuma venda registrada ainda")
    
    # ==================== LANÇAR COMPRA ====================
    elif opcao == "🛒 Lançar Compra":
        st.markdown("## 🛒 Lançar Nova Compra")
        
        with st.form("form_compra"):
            st.markdown("### Informações da Compra")
            
            valor = st.number_input(
                "💵 Valor Total da Compra (R$)",
                min_value=0.01,
                value=0.01,
                step=0.01,
                format="%.2f"
            )
            
            descricao = st.text_area(
                "📝 Descrição (opcional)",
                placeholder="Ex: Compra de materiais, embalagens, ingredientes..."
            )
            
            submitted = st.form_submit_button("✅ Registrar Compra", use_container_width=True)
        
        if submitted:
            if valor > 0:
                try:
                    inserir_compra(supabase, valor, descricao)
                    st.markdown(f"""
                        <div class='success-message'>
                            ✅ <strong>Compra registrada com sucesso!</strong><br>
                            Valor: R$ {valor:,.2f}
                        </div>
                    """, unsafe_allow_html=True)
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Erro ao registrar compra: {str(e)}")
            else:
                st.warning("⚠️ O valor deve ser maior que zero")
    
    # ==================== LANÇAR VENDA ====================
    elif opcao == "💰 Lançar Venda":
        st.markdown("## 💰 Lançar Nova Venda")
        
        with st.form("form_venda"):
            st.markdown("### Informações da Venda")
            
            col1, col2 = st.columns(2)
            
            with col1:
                produto = st.selectbox(
                    "🎁 Selecione a Box",
                    options=BOXES,
                    index=0
                )
            
            with col2:
                tamanho = st.selectbox(
                    "📏 Tamanho da Box",
                    options=list(TAMANHOS.keys()),
                    index=0,
                    help="O custo será registrado automaticamente"
                )
            
            # Mostrar o custo que será registrado
            custo_box = TAMANHOS[tamanho]
            st.info(f"💰 Custo desta box: R$ {custo_box:,.2f} (será registrado automaticamente nas compras)")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                quantidade = st.number_input(
                    "📦 Quantidade",
                    min_value=1,
                    value=1,
                    step=1
                )
            
            with col2:
                valor = st.number_input(
                    "💵 Valor Total da Venda (R$)",
                    min_value=0.01,
                    value=0.01,
                    step=0.01,
                    format="%.2f"
                )
            
            with col3:
                taxa_entrega = st.number_input(
                    "🚚 Taxa Entrega (R$)",
                    min_value=0.00,
                    value=0.00,
                    step=0.01,
                    format="%.2f",
                    help="Valor cobrado do cliente pela entrega"
                )
            
            submitted = st.form_submit_button("✅ Registrar Venda", use_container_width=True)
        
        if submitted:
            if valor > 0 and quantidade > 0:
                try:
                    # Registrar a venda
                    inserir_venda(supabase, produto, quantidade, valor, taxa_entrega, tamanho)
                    
                    # Registrar o custo da box automaticamente nas compras
                    custo_total = custo_box * quantidade
                    descricao_compra = f"Custo automático: {quantidade}x {tamanho} - {produto}"
                    inserir_compra(supabase, custo_total, descricao_compra)
                    
                    st.markdown(f"""
                        <div class='success-message'>
                            ✅ <strong>Venda registrada com sucesso!</strong><br>
                            {produto} ({tamanho}) - {quantidade} unidade(s)<br>
                            Valor Venda: R$ {valor:,.2f}<br>
                            Taxa Entrega: R$ {taxa_entrega:,.2f}<br>
                            💰 Custo registrado: R$ {custo_total:,.2f}
                        </div>
                    """, unsafe_allow_html=True)
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Erro ao registrar venda: {str(e)}")
            else:
                st.warning("⚠️ Valor e quantidade devem ser maiores que zero")
    
    # ==================== CUSTO ENTREGADOR ====================
    elif opcao == "🚚 Custo Entregador":
        st.markdown("## 🚚 Lançar Custo de Entregador")
        
        with st.form("form_entrega"):
            st.markdown("### Informações do Custo")
            
            custo = st.number_input(
                "💵 Valor Pago ao Entregador (R$)",
                min_value=0.01,
                value=0.01,
                step=0.01,
                format="%.2f",
                help="Quanto você pagou ao entregador"
            )
            
            descricao = st.text_area(
                "📝 Descrição (opcional)",
                placeholder="Ex: Entrega bairro X, 3 pedidos..."
            )
            
            submitted = st.form_submit_button("✅ Registrar Custo", use_container_width=True)
        
        if submitted:
            if custo > 0:
                try:
                    inserir_entrega(supabase, custo, descricao)
                    st.markdown(f"""
                        <div class='success-message'>
                            ✅ <strong>Custo de entrega registrado com sucesso!</strong><br>
                            Valor: R$ {custo:,.2f}
                        </div>
                    """, unsafe_allow_html=True)
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Erro ao registrar custo: {str(e)}")
            else:
                st.warning("⚠️ O valor deve ser maior que zero")
    
    # ==================== HISTÓRICO ====================
    elif opcao == "📋 Histórico":
        st.markdown("## 📋 Histórico de Movimentações")
        
        tab1, tab2, tab3 = st.tabs(["🛒 Compras", "💰 Vendas", "🚚 Entregas"])
        
        with tab1:
            st.markdown("### 🛒 Histórico de Compras")
            compras = buscar_compras(supabase, 100)
            
            if compras:
                # Total
                total = sum([float(c['valor_total']) for c in compras])
                st.markdown(f"**Total de Compras:** R$ {total:,.2f}")
                st.markdown("---")
                
                # Mostrar cada compra com botão de excluir
                for compra in compras:
                    col1, col2, col3, col4 = st.columns([2, 2, 3, 1])
                    
                    data_formatada = datetime.fromisoformat(compra['data'].replace('Z', '+00:00')).strftime('%d/%m/%Y %H:%M')
                    
                    with col1:
                        st.write(f"📅 {data_formatada}")
                    with col2:
                        st.write(f"💵 R$ {float(compra['valor_total']):,.2f}")
                    with col3:
                        st.write(f"📝 {compra.get('descricao', '-')}")
                    with col4:
                        if st.button("🗑️", key=f"del_compra_{compra['id']}", help="Excluir", use_container_width=True):
                            try:
                                excluir_compra(supabase, compra['id'])
                                st.success("✅ Compra excluída!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Erro: {str(e)}")
                    
                    st.markdown("---")
            else:
                st.info("📭 Nenhuma compra registrada ainda")
        
        with tab2:
            st.markdown("### 💰 Histórico de Vendas")
            vendas = buscar_vendas(supabase, 100)
            
            if vendas:
                # Resumo
                total = sum([float(v['valor_total']) for v in vendas])
                total_taxa = sum([float(v.get('taxa_entrega', 0)) for v in vendas])
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Total de Vendas:** R$ {total:,.2f}")
                with col2:
                    st.markdown(f"**Total Taxa Entrega:** R$ {total_taxa:,.2f}")
                
                st.markdown("---")
                
                # Mostrar cada venda com botão de excluir
                for venda in vendas:
                    col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 1.5, 1, 1.5, 1])
                    
                    data_formatada = datetime.fromisoformat(venda['data'].replace('Z', '+00:00')).strftime('%d/%m/%Y %H:%M')
                    
                    with col1:
                        st.write(f"📅 {data_formatada}")
                    with col2:
                        st.write(f"🎁 {venda['produto']}")
                    with col3:
                        st.write(f"📏 {venda.get('tamanho', 'N/A')}")
                    with col4:
                        st.write(f"📦 {venda['quantidade']}")
                    with col5:
                        st.write(f"💵 R$ {float(venda['valor_total']):,.2f}")
                    with col6:
                        if st.button("🗑️", key=f"del_venda_{venda['id']}", help="Excluir", use_container_width=True):
                            try:
                                excluir_venda(supabase, venda['id'])
                                st.success("✅ Venda excluída!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Erro: {str(e)}")
                    
                    st.markdown("---")
                
                # Resumo por produto
                st.markdown("#### 📊 Vendas por Produto")
                vendas_por_produto = {}
                for venda in vendas:
                    produto = venda['produto']
                    if produto not in vendas_por_produto:
                        vendas_por_produto[produto] = {'quantidade': 0, 'valor': 0}
                    vendas_por_produto[produto]['quantidade'] += venda['quantidade']
                    vendas_por_produto[produto]['valor'] += float(venda['valor_total'])
                
                for produto, dados in vendas_por_produto.items():
                    st.markdown(f"**{produto}:** {dados['quantidade']} unidades - R$ {dados['valor']:,.2f}")
            else:
                st.info("📭 Nenhuma venda registrada ainda")
        
        with tab3:
            st.markdown("### 🚚 Histórico de Custos de Entrega")
            entregas = buscar_entregas(supabase, 100)
            
            if entregas:
                # Total
                total = sum([float(e['custo_entregador']) for e in entregas])
                st.markdown(f"**Total Pago aos Entregadores:** R$ {total:,.2f}")
                st.markdown("---")
                
                # Mostrar cada entrega com botão de excluir
                for entrega in entregas:
                    col1, col2, col3, col4 = st.columns([2, 2, 3, 1])
                    
                    data_formatada = datetime.fromisoformat(entrega['data'].replace('Z', '+00:00')).strftime('%d/%m/%Y %H:%M')
                    
                    with col1:
                        st.write(f"📅 {data_formatada}")
                    with col2:
                        st.write(f"💵 R$ {float(entrega['custo_entregador']):,.2f}")
                    with col3:
                        st.write(f"📝 {entrega.get('descricao', '-')}")
                    with col4:
                        if st.button("🗑️", key=f"del_entrega_{entrega['id']}", help="Excluir", use_container_width=True):
                            try:
                                excluir_entrega(supabase, entrega['id'])
                                st.success("✅ Custo excluído!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Erro: {str(e)}")
                    
                    st.markdown("---")
            else:
                st.info("📭 Nenhum custo de entrega registrado ainda")

if __name__ == "__main__":
    main()
