import streamlit as st
from datetime import datetime
from supabase import create_client, Client
import pandas as pd
from PIL import Image
import xml.etree.ElementTree as ET
import requests
import re

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
            min-height: 140px;
            display: flex;
            flex-direction: column;
            justify-content: center;
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

# ==================== DETECÇÃO AUTOMÁTICA DE UNIDADE ====================
def detectar_unidade_material(nome_produto):
    """Detecta automaticamente a unidade de medida baseado no nome do produto"""
    nome_lower = nome_produto.lower()
    
    # Materiais em METRO
    palavras_metro = ['vinil', 'adesivo', 'tecido', 'papel', 'lona', 'banner', 'fita', 
                      'rolo', 'cetim', 'tnt', 'feltro', 'cordao', 'corda', 'barbante',
                      'ribbon', 'organza', 'tule']
    
    # Materiais em UNIDADE
    palavras_unidade = ['balao', 'balão', 'bubble', 'flor', 'caneca', 'xicara', 'xícara',
                        'copo', 'prato', 'chocolate', 'bombom', 'vela', 'rosa', 'girassol',
                        'orquidea', 'orquídea', 'tulipa', 'mini', 'chaveiro', 'imã', 'ima',
                        'tag', 'cartao', 'cartão', 'envelope']
    
    # Materiais em LITRO
    palavras_litro = ['tinta', 'cola', 'verniz', 'solvente', 'alcool', 'álcool', 
                      'thinner', 'agua', 'água', 'oleo', 'óleo', 'liquido', 'líquido']
    
    # Materiais em KG
    palavras_kg = ['acucar', 'açúcar', 'farinha', 'sal', 'pes', 'pés', 'granulado',
                   'granel', 'argila', 'massa', 'gesso']
    
    # Materiais em GRAMA
    palavras_grama = ['glitter', 'brilho', 'purpurina', 'confete', 'confeti']
    
    # Materiais em PACOTE
    palavras_pacote = ['pacote', 'embalagem', 'saco', 'sacola']
    
    # Verificar cada categoria
    for palavra in palavras_metro:
        if palavra in nome_lower:
            return 'metro'
    
    for palavra in palavras_litro:
        if palavra in nome_lower:
            return 'litro'
    
    for palavra in palavras_kg:
        if palavra in nome_lower:
            return 'kg'
    
    for palavra in palavras_grama:
        if palavra in nome_lower:
            return 'grama'
    
    for palavra in palavras_pacote:
        if palavra in nome_lower:
            return 'pacote'
    
    for palavra in palavras_unidade:
        if palavra in nome_lower:
            return 'unidade'
    
    # Padrão se não detectar nada
    return 'unidade'

# ==================== DETECÇÃO DE MATERIAIS SIMILARES ====================
def calcular_similaridade(texto1, texto2):
    """Calcula a similaridade entre dois textos (0 a 1)"""
    texto1 = texto1.lower().strip()
    texto2 = texto2.lower().strip()
    
    # Se for exatamente igual
    if texto1 == texto2:
        return 1.0
    
    # Remover palavras comuns que não agregam
    palavras_remover = ['unidade', 'unidades', 'un', 'pcs', 'peças', 'pacote', 'caixa', 
                        'kit', 'conjunto', 'com', 'de', 'para', 'em']
    
    def limpar_texto(texto):
        palavras = texto.split()
        palavras_filtradas = [p for p in palavras if p not in palavras_remover and not p.isdigit()]
        return ' '.join(palavras_filtradas)
    
    texto1_limpo = limpar_texto(texto1)
    texto2_limpo = limpar_texto(texto2)
    
    # Se um está contido no outro
    if texto1_limpo in texto2_limpo or texto2_limpo in texto1_limpo:
        return 0.8
    
    # Calcular palavras em comum
    palavras1 = set(texto1_limpo.split())
    palavras2 = set(texto2_limpo.split())
    
    if not palavras1 or not palavras2:
        return 0.0
    
    intersecao = palavras1.intersection(palavras2)
    uniao = palavras1.union(palavras2)
    
    similaridade = len(intersecao) / len(uniao)
    return similaridade

def buscar_materiais_similares(nome_novo, materiais_existentes, limiar=0.6):
    """Busca materiais similares na lista de materiais existentes"""
    similares = []
    
    for material in materiais_existentes:
        similaridade = calcular_similaridade(nome_novo, material['nome'])
        if similaridade >= limiar:
            similares.append({
                'material': material,
                'similaridade': similaridade
            })
    
    # Ordenar por similaridade (maior primeiro)
    similares.sort(key=lambda x: x['similaridade'], reverse=True)
    return similares

def calcular_custo_medio_ponderado(estoque_atual, custo_atual, qtd_nova, custo_novo):
    """Calcula o custo médio ponderado após nova compra"""
    valor_estoque_atual = estoque_atual * custo_atual
    valor_compra_nova = qtd_nova * custo_novo
    
    estoque_final = estoque_atual + qtd_nova
    
    if estoque_final == 0:
        return custo_novo
    
    custo_medio = (valor_estoque_atual + valor_compra_nova) / estoque_final
    return custo_medio

# ==================== BOXES PREDEFINIDAS ====================
BOXES = [
    "Box Café da manhã/tarde",
    "Box Chocolate",
    "Box Maternidade",
    "Box Casamento",
    "Box Aniversário",
    "Box Formatura",
    "Box de Flor com Caneca"
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

def buscar_xml_por_chave(chave_acesso):
    """Busca o XML da NF-e pela chave de acesso de 44 dígitos"""
    try:
        # Validar se tem 44 dígitos
        if len(chave_acesso) != 44 or not chave_acesso.isdigit():
            return {
                "sucesso": False,
                "mensagem": "A chave de acesso deve ter exatamente 44 dígitos numéricos"
            }
        
        # Extrair UF da chave (2 primeiros dígitos)
        uf_codigo = chave_acesso[:2]
        
        # Mapa de códigos de UF
        uf_map = {
            '35': 'SP', '33': 'RJ', '31': 'MG', '41': 'PR', '42': 'SC', '43': 'RS',
            '53': 'DF', '52': 'GO', '51': 'MT', '50': 'MS', '11': 'RO', '12': 'AC',
            '13': 'AM', '14': 'RR', '15': 'PA', '16': 'AP', '17': 'TO', '21': 'MA',
            '22': 'PI', '23': 'CE', '24': 'RN', '25': 'PB', '26': 'PE', '27': 'AL',
            '28': 'SE', '29': 'BA', '32': 'ES'
        }
        
        uf = uf_map.get(uf_codigo, 'Desconhecido')
        
        # Montar URL da SEFAZ (exemplo para SP)
        # Nota: Cada estado tem sua própria URL e pode requerer autenticação
        if uf == 'ES':
            url = f"https://app.sefaz.es.gov.br/ConsultaNFCe/qrcode.aspx"
            return {
                "sucesso": True,
                "mensagem": f"✅ Link da SEFAZ-ES gerado! Acesse para baixar o XML",
                "url": url,
                "chave": chave_acesso,
                "uf": uf,
                "instrucoes": f"1. Clique no link abaixo\n2. Digite a chave no campo indicado\n3. Clique em 'Consultar'\n4. Baixe o XML na página que abrir"
            }
        elif uf == 'SP':
            url = f"https://www.nfe.fazenda.sp.gov.br/NFCeConsultaPublica/Paginas/ConsultaPublica.aspx"
            return {
                "sucesso": True,
                "mensagem": f"✅ Link da SEFAZ-SP gerado! Acesse para baixar o XML",
                "url": url,
                "chave": chave_acesso,
                "uf": uf,
                "instrucoes": f"1. Clique no link abaixo\n2. Digite a chave no campo indicado\n3. Clique em 'Consultar'\n4. Baixe o XML na página que abrir"
            }
        else:
            # Para outros estados, retornar link genérico
            return {
                "sucesso": False,
                "mensagem": f"Para {uf}, use o QR Code do cupom ou acesse o site da SEFAZ-{uf}",
                "url": None,
                "chave": chave_acesso,
                "uf": uf
            }
        
        return {
            "sucesso": False,
            "mensagem": f"Para SP, acesse o Portal da Nota Fiscal Paulista ou use o QR Code do cupom",
            "url": url,
            "chave": chave_acesso,
            "uf": uf,
            "instrucoes": "O download automático por chave não está disponível devido às restrições de segurança da SEFAZ. Use o QR Code do cupom fiscal para obter o XML rapidamente."
        }
        
    except Exception as e:
        return {
            "sucesso": False,
            "mensagem": f"Erro ao processar chave: {str(e)}"
        }

def extrair_dados_html_nfce(html_content):
    """Extrai dados do HTML do DANFE quando o XML não está disponível"""
    try:
        if isinstance(html_content, bytes):
            try:
                html_content = html_content.decode('utf-8')
            except:
                html_content = html_content.decode('latin-1')
        
        # Extrair valor a pagar
        match_valor = re.search(r'Valor a pagar R\$.*?<span class="totalNumb txtMax">(\d+,\d+)</span>', html_content, re.DOTALL)
        valor_total = 0.0
        if match_valor:
            valor_str = match_valor.group(1).replace(',', '.')
            valor_total = float(valor_str)
        
        # Extrair nome do fornecedor
        match_fornecedor = re.search(r'<div id="u20" class="txtTopo">(.*?)</div>', html_content)
        nome_fornecedor = match_fornecedor.group(1).strip() if match_fornecedor else "Fornecedor"
        
        # Extrair data e número da nota
        match_data = re.search(r'<strong>Emissão: </strong>(\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2})', html_content)
        match_numero = re.search(r'<strong>Número: </strong>(\d+)', html_content)
        
        data_emissao = datetime.now()
        if match_data:
            try:
                data_emissao = datetime.strptime(match_data.group(1), '%d/%m/%Y %H:%M:%S')
            except:
                pass
        
        numero_nf = match_numero.group(1) if match_numero else ""
        
        # Extrair itens - formato específico SEFAZ-ES
        itens = []
        
        # Padrão para o formato usado pela SEFAZ-ES com spans Rqtd e RvlUnit
        pattern = r'<span class="txtTit">([^<]+)</span>.*?<span class="Rqtd">\s*<strong>Qtde\.?:\s*</strong>\s*(\d+(?:,\d+)?)\s*</span>.*?<span class="RvlUnit">\s*<strong>Vl\.\s*Unit\.?:\s*</strong>\s*([\d,]+)\s*</span>.*?Vl\.\s*Total.*?<span class="valor">([\d,]+)</span>'
        matches = re.finditer(pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            nome_prod = match.group(1).strip()
            qtd = float(match.group(2).replace(',', '.'))
            valor_unit = float(match.group(3).replace(',', '.'))
            valor_item = float(match.group(4).replace(',', '.'))
            
            itens.append({
                'produto': nome_prod,
                'quantidade': qtd,
                'valor_unitario': valor_unit,
                'valor_total': valor_item
            })
        
        # Criar descrição
        descricao = f"Compra {nome_fornecedor}"
        if numero_nf:
            descricao += f" - NF {numero_nf}"
        
        # Adicionar lista de itens na descrição
        if itens:
            descricao += "\n\nItens comprados:"
            for i, item in enumerate(itens, 1):
                descricao += f"\n{i}. {item['produto']} - {item['quantidade']:.0f} un - R$ {item['valor_total']:.2f}"
        
        return {
            "valor_total": valor_total,
            "data": data_emissao,
            "descricao": descricao,
            "itens": itens,
            "sucesso": True,
            "mensagem": "Dados extraídos do HTML do cupom com sucesso!"
        }
    except Exception as e:
        return {
            "valor_total": 0.0,
            "data": datetime.now(),
            "descricao": "",
            "itens": [],
            "sucesso": False,
            "mensagem": f"Erro ao extrair dados do HTML: {str(e)}"
        }

def extrair_dados_xml_nfe_v2(xml_content):
    """Extrai dados relevantes do XML da NF-e"""
    try:
        # Se for bytes, decodificar
        if isinstance(xml_content, bytes):
            try:
                xml_content = xml_content.decode('utf-8')
            except:
                xml_content = xml_content.decode('latin-1')
        
        # Limpar o XML de possíveis problemas
        # Remover BOM (Byte Order Mark)
        xml_content = xml_content.replace('\ufeff', '')
        
        # Remover possíveis tags HTML
        xml_content = xml_content.replace('&nbsp;', ' ')
        xml_content = xml_content.replace('&amp;', '&')
        xml_content = xml_content.replace('&lt;', '<')
        xml_content = xml_content.replace('&gt;', '>')
        
        # Tentar encontrar o início do XML se houver HTML antes
        if '<?xml' in xml_content:
            xml_content = xml_content[xml_content.index('<?xml'):]
        elif '<nfeProc' in xml_content:
            xml_content = '<?xml version="1.0" encoding="UTF-8"?>' + xml_content[xml_content.index('<nfeProc'):]
        elif '<NFe' in xml_content:
            xml_content = '<?xml version="1.0" encoding="UTF-8"?>' + xml_content[xml_content.index('<NFe'):]
        
        # Remover qualquer coisa depois da tag de fechamento
        if '</nfeProc>' in xml_content:
            xml_content = xml_content[:xml_content.index('</nfeProc>') + len('</nfeProc>')]
        elif '</NFe>' in xml_content:
            xml_content = xml_content[:xml_content.index('</NFe>') + len('</NFe>')]
        
        # Parse do XML
        root = ET.fromstring(xml_content)
        
        # Namespace da NF-e
        ns_url = 'http://www.portalfiscal.inf.br/nfe'
        
        # Se root é nfeProc, buscar o elemento NFe
        if 'nfeProc' in root.tag:
            nfe_element = root.find('{%s}NFe' % ns_url)
            if nfe_element is not None:
                root = nfe_element
        
        # Se root é NFe, buscar dentro de infNFe
        if 'NFe' in root.tag:
            infnfe_element = root.find('{%s}infNFe' % ns_url)
            if infnfe_element is not None:
                root = infnfe_element
        
        # Extrair valor total - buscar diretamente com namespace completo
        valor_element = root.find('.//{%s}vNF' % ns_url)
        if valor_element is None:
            valor_element = root.find('.//vNF')
        valor_total = float(valor_element.text) if valor_element is not None else 0.0
        
        # Extrair data de emissão
        data_element = root.find('.//{%s}dhEmi' % ns_url)
        if data_element is None:
            data_element = root.find('.//dhEmi')
        if data_element is not None:
            data_str = data_element.text.replace('Z', '+00:00')
            try:
                data_emissao = datetime.fromisoformat(data_str)
            except:
                data_emissao = datetime.now()
        else:
            data_emissao = datetime.now()
        
        # Extrair nome do fornecedor
        nome_element = root.find('.//{%s}xFant' % ns_url)
        if nome_element is None:
            nome_element = root.find('.//{%s}xNome' % ns_url)
        if nome_element is None:
            nome_element = root.find('.//xFant')
        if nome_element is None:
            nome_element = root.find('.//xNome')
        nome_fornecedor = nome_element.text if nome_element is not None else "Fornecedor"
        
        # Extrair número da nota
        nf_element = root.find('.//{%s}nNF' % ns_url)
        if nf_element is None:
            nf_element = root.find('.//nNF')
        numero_nf = nf_element.text if nf_element is not None else ""
        
        # Extrair itens da nota
        itens = []
        # Buscar produtos diretamente
        det_elements = root.findall('.//{%s}det' % ns_url)
        if not det_elements:
            det_elements = root.findall('.//det')
        
        for det in det_elements:
            # Buscar prod
            prod = det.find('{%s}prod' % ns_url)
            if prod is None:
                prod = det.find('prod')
            
            if prod is not None:
                # Buscar dados do produto
                nome_prod = prod.find('{%s}xProd' % ns_url)
                if nome_prod is None:
                    nome_prod = prod.find('xProd')
                
                qtd_prod = prod.find('{%s}qCom' % ns_url)
                if qtd_prod is None:
                    qtd_prod = prod.find('qCom')
                
                valor_unit = prod.find('{%s}vUnCom' % ns_url)
                if valor_unit is None:
                    valor_unit = prod.find('vUnCom')
                
                valor_prod = prod.find('{%s}vProd' % ns_url)
                if valor_prod is None:
                    valor_prod = prod.find('vProd')
                
                if nome_prod is not None:
                    nome_completo = nome_prod.text
                    item = {
                        'nome': nome_completo[:50],
                        'descricao': nome_completo,
                        'quantidade': float(qtd_prod.text) if qtd_prod is not None else 0,
                        'valor_unitario': float(valor_unit.text) if valor_unit is not None else 0,
                        'valor_total': float(valor_prod.text) if valor_prod is not None else 0
                    }
                    itens.append(item)
        
        # Criar descrição
        descricao = f"Compra {nome_fornecedor}"
        if numero_nf:
            descricao += f" - NF {numero_nf}"
        
        # Adicionar lista de itens na descrição
        if itens:
            descricao += "\n\nItens comprados:"
            for i, item in enumerate(itens, 1):
                descricao += f"\n{i}. {item['nome']} - {item['quantidade']:.0f} un - R$ {item['valor_total']:.2f}"
        
        return {
            "valor_total": valor_total,
            "data": data_emissao,
            "descricao": descricao,
            "fornecedor": nome_fornecedor,
            "itens": itens,
            "sucesso": True,
            "mensagem": f"XML lido com sucesso! {len(itens)} produtos encontrados.",
            "tipo_documento": "NF-e"
        }
    except ET.ParseError as e:
        return {
            "valor_total": 0.0,
            "data": datetime.now(),
            "descricao": "",
            "itens": [],
            "sucesso": False,
            "mensagem": f"Erro ao processar XML: Formato inválido. {str(e)}"
        }
    except Exception as e:
        return {
            "valor_total": 0.0,
            "data": datetime.now(),
            "descricao": "",
            "itens": [],
            "sucesso": False,
            "mensagem": f"Erro ao ler XML: {str(e)}"
        }

def inserir_compra(supabase: Client, valor_total: float, descricao: str = "", data_compra=None, num_parcelas: int = 1):
    """Insere uma nova compra no banco e cria as parcelas"""
    data_base = data_compra if data_compra else datetime.now()
    
    data = {
        "data": data_base.isoformat(),
        "valor_total": valor_total,
        "descricao": descricao
    }
    result = supabase.table("singelo_compras").insert(data).execute()
    compra_id = result.data[0]['id']
    
    # Criar parcelas com vencimento sempre no dia 12 (apenas se num_parcelas > 0)
    if num_parcelas == 0:
        # Não criar parcelas - compra foi paga à vista
        pass
    elif num_parcelas > 1:
        # Se a compra foi feita após o dia 12, começar no próximo mês
        meses_adicionar = 1 if data_base.day > 12 else 0
        
        valor_parcela = valor_total / num_parcelas
        for i in range(num_parcelas):
            # Adicionar i meses à data base (+ ajuste se comprou após dia 12)
            mes_vencimento = data_base.month + i + meses_adicionar
            ano_vencimento = data_base.year
            
            # Ajustar ano se passar de dezembro
            while mes_vencimento > 12:
                mes_vencimento -= 12
                ano_vencimento += 1
            
            # Sempre usar dia 12 como vencimento (dia do fechamento do cartão)
            try:
                data_vencimento = datetime(ano_vencimento, mes_vencimento, 12)
            except ValueError:
                # Se o mês não tem dia 12 (não deve acontecer), usar último dia do mês
                from calendar import monthrange
                ultimo_dia = monthrange(ano_vencimento, mes_vencimento)[1]
                data_vencimento = datetime(ano_vencimento, mes_vencimento, min(12, ultimo_dia))
            
            parcela_data = {
                "compra_id": compra_id,
                "numero_parcela": i + 1,
                "total_parcelas": num_parcelas,
                "valor_parcela": valor_parcela,
                "data_vencimento": data_vencimento.isoformat(),
                "status": "pendente",
                "descricao": descricao
            }
            supabase.table("singelo_parcelas_compras").insert(parcela_data).execute()
    else:
        # Compra à vista - criar uma única parcela com vencimento no dia 12
        # Se a compra foi após o dia 12, vencimento vai para o próximo mês
        mes_vencimento = data_base.month + (1 if data_base.day > 12 else 0)
        ano_vencimento = data_base.year
        
        if mes_vencimento > 12:
            mes_vencimento = 1
            ano_vencimento += 1
        
        try:
            data_vencimento = datetime(ano_vencimento, mes_vencimento, 12)
        except ValueError:
            from calendar import monthrange
            ultimo_dia = monthrange(ano_vencimento, mes_vencimento)[1]
            data_vencimento = datetime(ano_vencimento, mes_vencimento, min(12, ultimo_dia))
        
        parcela_data = {
            "compra_id": compra_id,
            "numero_parcela": 1,
            "total_parcelas": 1,
            "valor_parcela": valor_total,
            "data_vencimento": data_vencimento.isoformat(),
            "status": "pendente",
            "descricao": descricao
        }
        supabase.table("singelo_parcelas_compras").insert(parcela_data).execute()
    
    return result

def inserir_itens_compra(supabase: Client, compra_id: int, itens: list):
    """Insere os itens individuais de uma compra na tabela de itens"""
    try:
        for item in itens:
            item_data = {
                "compra_id": compra_id,
                "nome_produto": item.get('nome', ''),
                "descricao": item.get('descricao', ''),
                "quantidade": float(item.get('quantidade', 0)),
                "valor_unitario": float(item.get('valor_unitario', 0)),
                "valor_total": float(item.get('valor_total', 0))
            }
            supabase.table("singelo_itens_compras").insert(item_data).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao inserir itens: {str(e)}")
        return False

def inserir_compra_com_itens(supabase: Client, valor_total: float, descricao: str, itens: list, data_compra=None, num_parcelas: int = 1, fornecedor: str = ""):
    """Insere uma compra com seus itens individuais"""
    # Adicionar fornecedor à descrição se fornecido
    if fornecedor:
        descricao = f"Fornecedor: {fornecedor}\n{descricao}"
    
    # Inserir a compra
    result = inserir_compra(supabase, valor_total, descricao, data_compra, num_parcelas)
    compra_id = result.data[0]['id']
    
    # Inserir os itens
    if itens:
        inserir_itens_compra(supabase, compra_id, itens)
    
    return result

def extrair_dados_xml_nfe(xml_content):
    """Extrai dados de uma NF-e (Nota Fiscal Eletrônica) completa"""
    try:
        import xml.etree.ElementTree as ET
        
        # Parse do XML
        if isinstance(xml_content, bytes):
            root = ET.fromstring(xml_content.decode('utf-8'))
        else:
            root = ET.fromstring(xml_content)
        
        # Namespace da NF-e
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
        
        # Buscar informações da nota
        inf_nfe = root.find('.//nfe:infNFe', ns)
        if not inf_nfe:
            # Tentar sem namespace
            inf_nfe = root.find('.//infNFe')
        
        # Extrair fornecedor
        fornecedor = ""
        emit = root.find('.//nfe:emit', ns) or root.find('.//emit')
        if emit:
            nome_emit = emit.find('.//nfe:xNome', ns) or emit.find('.//xNome')
            if nome_emit is not None:
                fornecedor = nome_emit.text
        
        # Extrair produtos
        itens = []
        produtos = root.findall('.//nfe:det', ns) or root.findall('.//det')
        
        for produto in produtos:
            prod = produto.find('.//nfe:prod', ns) or produto.find('.//prod')
            if prod:
                nome = prod.find('.//nfe:xProd', ns) or prod.find('.//xProd')
                quantidade = prod.find('.//nfe:qCom', ns) or prod.find('.//qCom')
                valor_unit = prod.find('.//nfe:vUnCom', ns) or prod.find('.//vUnCom')
                codigo = prod.find('.//nfe:cProd', ns) or prod.find('.//cProd')
                
                if nome is not None and quantidade is not None and valor_unit is not None:
                    qtd = float(quantidade.text)
                    v_unit = float(valor_unit.text)
                    
                    itens.append({
                        'nome': nome.text,
                        'descricao': f"Cód: {codigo.text if codigo is not None else 'N/A'}",
                        'quantidade': qtd,
                        'valor_unitario': v_unit,
                        'valor_total': qtd * v_unit
                    })
        
        # Calcular valor total
        valor_total = sum([item['valor_total'] for item in itens])
        
        # Extrair data da nota
        data_emissao = datetime.now()
        dh_emit = root.find('.//nfe:dhEmi', ns) or root.find('.//dhEmi')
        if dh_emit is not None:
            try:
                data_emissao = datetime.fromisoformat(dh_emit.text.replace('Z', '+00:00'))
            except:
                pass
        
        return {
            "sucesso": True,
            "mensagem": f"NF-e processada com sucesso! {len(itens)} produtos encontrados.",
            "valor_total": valor_total,
            "fornecedor": fornecedor,
            "data": data_emissao,
            "itens": itens,
            "tipo_documento": "NF-e"
        }
        
    except Exception as e:
        return {
            "sucesso": False,
            "mensagem": f"Erro ao processar NF-e: {str(e)}",
            "valor_total": 0,
            "fornecedor": "",
            "data": datetime.now(),
            "itens": [],
            "tipo_documento": "NF-e"
        }

def buscar_parcelas_pendentes(supabase: Client, data_inicio=None, data_fim=None):
    """Busca parcelas com vencimento até o final do período (inclui parcelas futuras do mês)"""
    query = supabase.table("singelo_parcelas_compras").select("*")
    
    if data_inicio:
        query = query.gte("data_vencimento", data_inicio.isoformat())
    if data_fim:
        # Buscar até o final do mês da data_fim para pegar parcelas futuras do mês
        from calendar import monthrange
        ultimo_dia = monthrange(data_fim.year, data_fim.month)[1]
        data_fim_mes = datetime(data_fim.year, data_fim.month, ultimo_dia, 23, 59, 59)
        query = query.lte("data_vencimento", data_fim_mes.isoformat())
    
    result = query.order("data_vencimento", desc=False).execute()
    return result.data

def marcar_parcela_paga(supabase: Client, parcela_id: int):
    """Marca uma parcela como paga"""
    data = {
        "status": "pago",
        "data_pagamento": datetime.now().isoformat()
    }
    result = supabase.table("singelo_parcelas_compras").update(data).eq("id", parcela_id).execute()
    return result

def marcar_parcela_pendente(supabase: Client, parcela_id: int):
    """Marca uma parcela como pendente"""
    data = {
        "status": "pendente",
        "data_pagamento": None
    }
    result = supabase.table("singelo_parcelas_compras").update(data).eq("id", parcela_id).execute()
    return result

def buscar_cep(cep: str):
    """Busca informações de endereço pelo CEP usando ViaCEP"""
    try:
        # Remover formatação do CEP
        cep_limpo = ''.join(filter(str.isdigit, cep))
        
        if len(cep_limpo) != 8:
            return {
                "sucesso": False,
                "mensagem": "CEP deve ter 8 dígitos"
            }
        
        # Buscar na API ViaCEP
        url = f"https://viacep.com.br/ws/{cep_limpo}/json/"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            dados = response.json()
            
            if 'erro' in dados:
                return {
                    "sucesso": False,
                    "mensagem": "CEP não encontrado"
                }
            
            return {
                "sucesso": True,
                "cep": cep_limpo,
                "logradouro": dados.get('logradouro', ''),
                "bairro": dados.get('bairro', ''),
                "cidade": dados.get('localidade', ''),
                "uf": dados.get('uf', ''),
                "complemento": dados.get('complemento', '')
            }
        else:
            return {
                "sucesso": False,
                "mensagem": "Erro ao consultar CEP"
            }
    except Exception as e:
        return {
            "sucesso": False,
            "mensagem": f"Erro: {str(e)}"
        }

def inserir_venda(supabase: Client, produto: str, quantidade: int, valor_total: float, taxa_entrega: float = 0, 
                  tamanho: str = "", data_entrega=None, cep: str = "", logradouro: str = "", numero: str = "", 
                  complemento: str = "", bairro: str = "", cidade: str = "", uf: str = ""):
    """Insere uma nova venda no banco"""
    data = {
        "data": datetime.now().isoformat(),
        "produto": produto,
        "quantidade": quantidade,
        "valor_total": valor_total,
        "taxa_entrega": taxa_entrega,
        "tamanho": tamanho,
        "data_entrega": data_entrega.isoformat() if data_entrega else None,
        "cep": cep,
        "logradouro": logradouro,
        "numero": numero,
        "complemento": complemento,
        "bairro": bairro,
        "cidade": cidade,
        "uf": uf
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

def atualizar_compra(supabase: Client, compra_id: int, valor_total: float, descricao: str = ""):
    """Atualiza uma compra existente"""
    data = {
        "valor_total": valor_total,
        "descricao": descricao
    }
    result = supabase.table("singelo_compras").update(data).eq("id", compra_id).execute()
    return result

def atualizar_venda(supabase: Client, venda_id: int, produto: str, quantidade: int, valor_total: float, 
                    taxa_entrega: float = 0, tamanho: str = "", data_entrega=None, cep: str = "", 
                    logradouro: str = "", numero: str = "", complemento: str = "", bairro: str = "", 
                    cidade: str = "", uf: str = ""):
    """Atualiza uma venda existente"""
    data = {
        "produto": produto,
        "quantidade": quantidade,
        "valor_total": valor_total,
        "taxa_entrega": taxa_entrega,
        "tamanho": tamanho,
        "data_entrega": data_entrega.isoformat() if data_entrega else None,
        "cep": cep,
        "logradouro": logradouro,
        "numero": numero,
        "complemento": complemento,
        "bairro": bairro,
        "cidade": cidade,
        "uf": uf
    }
    result = supabase.table("singelo_vendas").update(data).eq("id", venda_id).execute()
    return result

def atualizar_entrega(supabase: Client, entrega_id: int, custo_entregador: float, descricao: str = ""):
    """Atualiza um custo de entrega existente"""
    data = {
        "custo_entregador": custo_entregador,
        "descricao": descricao
    }
    result = supabase.table("singelo_entregas").update(data).eq("id", entrega_id).execute()
    return result

def recalcular_parcelas(supabase: Client, compra_id: int, novo_valor_total: float, novo_num_parcelas: int, data_compra):
    """Recalcula e atualiza todas as parcelas de uma compra"""
    # Excluir parcelas antigas
    supabase.table("singelo_parcelas_compras").delete().eq("compra_id", compra_id).execute()
    
    # Criar novas parcelas com vencimento sempre no dia 12
    # Se a compra foi feita após o dia 12, começar no próximo mês
    meses_adicionar = 1 if data_compra.day > 12 else 0
    
    valor_parcela = novo_valor_total / novo_num_parcelas
    for i in range(novo_num_parcelas):
        # Adicionar i meses à data base (+ ajuste se comprou após dia 12)
        mes_vencimento = data_compra.month + i + meses_adicionar
        ano_vencimento = data_compra.year
        
        # Ajustar ano se passar de dezembro
        while mes_vencimento > 12:
            mes_vencimento -= 12
            ano_vencimento += 1
        
        # Sempre usar dia 12 como vencimento (dia do fechamento do cartão)
        try:
            data_vencimento = datetime(ano_vencimento, mes_vencimento, 12)
        except ValueError:
            # Se o mês não tem dia 12 (não deve acontecer), usar último dia do mês
            from calendar import monthrange
            ultimo_dia = monthrange(ano_vencimento, mes_vencimento)[1]
            data_vencimento = datetime(ano_vencimento, mes_vencimento, min(12, ultimo_dia))
        
        parcela_data = {
            "compra_id": compra_id,
            "numero_parcela": i + 1,
            "total_parcelas": novo_num_parcelas,
            "valor_parcela": valor_parcela,
            "data_vencimento": data_vencimento.isoformat(),
            "status": "pendente",
            "descricao": ""
        }
        supabase.table("singelo_parcelas_compras").insert(parcela_data).execute()
    
    return True

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

def calcular_resumo(supabase: Client, data_inicio=None, data_fim=None):
    """Calcula o resumo financeiro usando parcelas por vencimento e custos automáticos por data"""
    try:
        # Buscar PARCELAS do período (por data de vencimento)
        query_parcelas = supabase.table("singelo_parcelas_compras").select("valor_parcela, data_vencimento, compra_id")
        
        # Buscar TODAS as compras do período
        query_compras = supabase.table("singelo_compras").select("id, valor_total, data, descricao")
        
        query_vendas = supabase.table("singelo_vendas").select("valor_total, taxa_entrega, data")
        query_entregas = supabase.table("singelo_entregas").select("custo_entregador, data")
        
        if data_inicio:
            query_parcelas = query_parcelas.gte("data_vencimento", data_inicio.isoformat())
            query_compras = query_compras.gte("data", data_inicio.isoformat())
            query_vendas = query_vendas.gte("data", data_inicio.isoformat())
            query_entregas = query_entregas.gte("data", data_inicio.isoformat())
        
        if data_fim:
            # Incluir o dia final completo (até 23:59:59)
            data_fim_final = datetime.combine(data_fim, datetime.max.time())
            query_parcelas = query_parcelas.lte("data_vencimento", data_fim_final.isoformat())
            query_compras = query_compras.lte("data", data_fim_final.isoformat())
            query_vendas = query_vendas.lte("data", data_fim_final.isoformat())
            query_entregas = query_entregas.lte("data", data_fim_final.isoformat())
        
        parcelas = query_parcelas.execute()
        compras = query_compras.execute()
        vendas = query_vendas.execute()
        entregas = query_entregas.execute()
        
        # Separar custos automáticos das compras normais
        custos_auto = [c for c in compras.data if c.get('descricao', '').startswith('Custo automático:')] if compras.data else []
        ids_custos_auto = [c['id'] for c in custos_auto]
        
        # Filtrar parcelas que NÃO são de custos automáticos
        parcelas_normais = [p for p in parcelas.data if p['compra_id'] not in ids_custos_auto] if parcelas.data else []
        
        # Calcular total de parcelas normais (compras de cartão de crédito)
        total_compras_cartao = sum([float(p['valor_parcela']) for p in parcelas_normais])
        
        # Calcular total de custos automáticos (valor total, não parcela)
        total_custos_auto = sum([float(c['valor_total']) for c in custos_auto])
        
        # Total de compras = parcelas normais + custos automáticos
        total_compras = total_compras_cartao + total_custos_auto
        
        total_custo_entregador = sum([float(e['custo_entregador']) for e in entregas.data]) if entregas.data else 0
        
        # Total de vendas = valor da venda + taxa de entrega cobrada do cliente
        total_vendas = sum([float(v['valor_total']) + float(v.get('taxa_entrega', 0)) for v in vendas.data]) if vendas.data else 0
        total_taxa_entrega_cobrada = sum([float(v.get('taxa_entrega', 0)) for v in vendas.data]) if vendas.data else 0
        
        lucro_entregas = total_taxa_entrega_cobrada - total_custo_entregador
        lucro = total_vendas - total_compras
        
        return {
            "total_compras": total_compras,
            "total_compras_cartao": total_compras_cartao,
            "total_custos_auto": total_custos_auto,
            "total_vendas": total_vendas,
            "total_taxa_entrega_cobrada": total_taxa_entrega_cobrada,
            "total_custo_entregador": total_custo_entregador,
            "lucro_entregas": lucro_entregas,
            "lucro": lucro
        }
    except Exception as e:
        return {
            "total_compras": 0,
            "total_compras_cartao": 0,
            "total_custos_auto": 0,
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
            ["📈 Dashboard", "🛒 Lançar Compra", "💰 Lançar Venda", "🚚 Custo Entregador", "💳 Contas a Pagar", "📦 Custos Produtos", "🧾 Ficha Técnica", "📋 Histórico"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.markdown("### ℹ️ Sobre")
        st.markdown("Sistema de gestão para **Singelo Gesto**")
        st.markdown("Box de Luxo Personalizadas")
    
    # ==================== DASHBOARD ====================
    if opcao == "📈 Dashboard":
        st.markdown("## 📈 Dashboard Financeiro")
        
        # Tabs principais do dashboard
        tab1, tab2 = st.tabs(["💰 Resumo Financeiro", "📊 Análise de Lucro"])
        
        with tab1:
            # Filtros de período
            st.markdown("### 📅 Filtrar por Período")
            col1, col2, col3 = st.columns([2, 2, 1])
            
            # Data padrão: dia 12 do mês atual até dia 12 do próximo mês
            hoje = datetime.now()
            data_inicio_padrao = datetime(hoje.year, hoje.month, 12)
            
            # Calcular dia 12 do próximo mês
            mes_fim = hoje.month + 1
            ano_fim = hoje.year
            if mes_fim > 12:
                mes_fim = 1
                ano_fim += 1
            data_fim_padrao = datetime(ano_fim, mes_fim, 12)
            
            with col1:
                data_inicio = st.date_input(
                    "Data Início",
                    value=data_inicio_padrao,
                    format="DD/MM/YYYY",
                    help="Data de início do período (padrão: dia 12 do mês atual)",
                    key="data_inicio_dash"
                )
            
            with col2:
                data_fim = st.date_input(
                    "Data Fim",
                    value=data_fim_padrao,
                    format="DD/MM/YYYY",
                    help="Data de fim do período (padrão: dia 12 do próximo mês)",
                    key="data_fim_dash"
                )
            
            with col3:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🔄 Limpar Filtros", key="limpar_filtros"):
                    st.rerun()
            
            # Converter None para None explicitamente
            data_inicio_filtro = data_inicio if data_inicio else None
            data_fim_filtro = data_fim if data_fim else None
            
            if data_inicio_filtro and data_fim_filtro and data_inicio_filtro > data_fim_filtro:
                st.error("❌ A data de início deve ser anterior à data de fim!")
            
            # Mostrar período selecionado
            if data_inicio_filtro or data_fim_filtro:
                periodo_texto = "Período: "
                if data_inicio_filtro:
                    periodo_texto += f"de {data_inicio_filtro.strftime('%d/%m/%Y')}"
                if data_fim_filtro:
                    periodo_texto += f" até {data_fim_filtro.strftime('%d/%m/%Y')}"
                st.info(f"📊 {periodo_texto}")
            else:
                st.info("📊 Mostrando todos os dados")
        
        st.markdown("---")
        
        resumo = calcular_resumo(supabase, data_inicio_filtro, data_fim_filtro)
        
        # Linha 1: Compras Cartão, Custos Automáticos, Vendas e Lucro
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
                <div class='metric-card' style='background: #8B4513;'>
                    <h3 style='font-size: 1.3rem;'>💳 Cartão Crédito</h3>
                    <h2>R$ {resumo['total_compras_cartao']:,.2f}</h2>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
                <div class='metric-card' style='background: #D2691E;'>
                    <h3>📝 Custos Box</h3>
                    <h2>R$ {resumo['total_custos_auto']:,.2f}</h2>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
                <div class='metric-card'>
                    <h3>💰 Total Vendas</h3>
                    <h2>R$ {resumo['total_vendas']:,.2f}</h2>
                </div>
            """, unsafe_allow_html=True)
        
        with col4:
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
        
        # ===== TAB 2: ANÁLISE DE LUCRO =====
        with tab2:
            st.markdown("### 📊 Análise de Lucro por Produto")
            
            try:
                # Buscar todas as fichas técnicas
                fichas = supabase.table("singelo_fichas_tecnicas").select("*, singelo_materiais(*)").execute()
                
                if fichas.data:
                    # Calcular custo de produção de cada produto
                    custos_produtos = {}
                    
                    for item in fichas.data:
                        produto = item['produto']
                        material = item['singelo_materiais']
                        quantidade = float(item['quantidade'])
                        custo_unit = float(material['custo_unitario'])
                        custo_item = quantidade * custo_unit
                        
                        if produto not in custos_produtos:
                            custos_produtos[produto] = {
                                'custo_total': 0,
                                'materiais': []
                            }
                        
                        custos_produtos[produto]['custo_total'] += custo_item
                        custos_produtos[produto]['materiais'].append({
                            'nome': material['nome'],
                            'quantidade': quantidade,
                            'unidade': material['unidade_medida'],
                            'custo': custo_item
                        })
                    
                    # Buscar vendas para comparar
                    vendas = supabase.table("singelo_vendas").select("*").execute()
                    
                    # Calcular preço médio de venda por produto
                    precos_venda = {}
                    qtd_vendas = {}
                    
                    if vendas.data:
                        for venda in vendas.data:
                            produto = venda['produto']
                            valor = float(venda['valor_total'])
                            qtd = int(venda['quantidade'])
                            
                            if produto not in precos_venda:
                                precos_venda[produto] = []
                                qtd_vendas[produto] = 0
                            
                            precos_venda[produto].append(valor / qtd)
                            qtd_vendas[produto] += qtd
                    
                    # Mostrar análise por produto
                    st.markdown("#### 💰 Margem de Lucro por Box")
                    
                    produtos_com_lucro = []
                    
                    for produto, dados in custos_produtos.items():
                        custo_producao = dados['custo_total']
                        
                        # Buscar preço de venda
                        if produto in precos_venda and precos_venda[produto]:
                            preco_medio_venda = sum(precos_venda[produto]) / len(precos_venda[produto])
                            lucro_unitario = preco_medio_venda - custo_producao
                            margem_pct = (lucro_unitario / preco_medio_venda * 100) if preco_medio_venda > 0 else 0
                            
                            # Determinar cor baseado na margem
                            if margem_pct >= 40:
                                cor = "#28A745"  # Verde
                                status = "✅ Ótima"
                            elif margem_pct >= 25:
                                cor = "#FFC107"  # Amarelo
                                status = "⚠️ Boa"
                            else:
                                cor = "#DC3545"  # Vermelho
                                status = "❌ Baixa"
                            
                            produtos_com_lucro.append({
                                'produto': produto,
                                'custo': custo_producao,
                                'preco': preco_medio_venda,
                                'lucro': lucro_unitario,
                                'margem': margem_pct,
                                'cor': cor,
                                'status': status,
                                'qtd_vendida': qtd_vendas[produto]
                            })
                        else:
                            # Produto sem vendas ainda
                            produtos_com_lucro.append({
                                'produto': produto,
                                'custo': custo_producao,
                                'preco': 0,
                                'lucro': 0,
                                'margem': 0,
                                'cor': "#6C757D",
                                'status': "⚪ Sem vendas",
                                'qtd_vendida': 0
                            })
                    
                    # Ordenar por margem (maior primeiro)
                    produtos_com_lucro.sort(key=lambda x: x['margem'], reverse=True)
                    
                    # Mostrar cards de produtos
                    for prod in produtos_com_lucro:
                        with st.expander(f"{prod['status']} **{prod['produto']}** - Margem: {prod['margem']:.1f}%"):
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric("💵 Custo Produção", f"R$ {prod['custo']:.2f}")
                            with col2:
                                st.metric("💰 Preço Venda", f"R$ {prod['preco']:.2f}")
                            with col3:
                                st.metric("📊 Lucro/Unidade", f"R$ {prod['lucro']:.2f}")
                            with col4:
                                st.metric("📈 Margem", f"{prod['margem']:.1f}%")
                            
                            if prod['qtd_vendida'] > 0:
                                lucro_total = prod['lucro'] * prod['qtd_vendida']
                                st.info(f"📦 Vendidas: **{prod['qtd_vendida']}** unidades | 💰 Lucro total: **R$ {lucro_total:.2f}**")
                            
                            # Mostrar composição de custos
                            st.markdown("**Composição de custos:**")
                            materiais_info = custos_produtos[prod['produto']]['materiais']
                            for mat in materiais_info:
                                percentual = (mat['custo'] / prod['custo'] * 100) if prod['custo'] > 0 else 0
                                st.write(f"- {mat['nome']}: R$ {mat['custo']:.2f} ({percentual:.1f}%)")
                    
                    # Alertas e recomendações
                    st.markdown("---")
                    st.markdown("### ⚠️ Alertas e Recomendações")
                    
                    alertas = []
                    
                    for prod in produtos_com_lucro:
                        if prod['margem'] < 25 and prod['qtd_vendida'] > 0:
                            alertas.append(f"🔴 **{prod['produto']}**: Margem muito baixa ({prod['margem']:.1f}%). Considere aumentar o preço ou reduzir custos.")
                        elif prod['margem'] == 0 and prod['qtd_vendida'] == 0:
                            alertas.append(f"⚪ **{prod['produto']}**: Produto sem vendas ainda. Custo de produção: R$ {prod['custo']:.2f}")
                    
                    if alertas:
                        for alerta in alertas:
                            st.warning(alerta)
                    else:
                        st.success("✅ Todas as margens estão saudáveis!")
                    
                    # Gráfico de margem de lucro
                    st.markdown("---")
                    st.markdown("### 📊 Visualização de Margens")
                    
                    import pandas as pd
                    df_margens = pd.DataFrame([
                        {
                            "Produto": p['produto'],
                            "Margem (%)": p['margem'],
                            "Lucro (R$)": p['lucro']
                        }
                        for p in produtos_com_lucro if p['qtd_vendida'] > 0
                    ])
                    
                    if not df_margens.empty:
                        st.bar_chart(df_margens.set_index("Produto")["Margem (%)"])
                    else:
                        st.info("Sem dados de vendas para exibir gráfico")
                    
                else:
                    st.warning("⚠️ Nenhuma ficha técnica cadastrada ainda. Vá em 🧾 Ficha Técnica para cadastrar os custos de produção!")
            
            except Exception as e:
                st.error(f"Erro ao carregar análise: {str(e)}")
                st.info("Certifique-se de que as tabelas de materiais e fichas técnicas estão criadas no Supabase.")
    
    # ==================== LANÇAR COMPRA ====================
    elif opcao == "🛒 Lançar Compra":
        st.markdown("## 🛒 Lançar Nova Compra")
        
        # Tabs para escolher entre manual, XML e chave de acesso
        tab1, tab2, tab3 = st.tabs(["✍️ Digitar Manualmente", "📄 Importar Documento", "🔑 Buscar por Chave"])
        
        with tab1:
            st.markdown("### ✍️ Cadastro Manual de Compra")
            
            # Inicializar session state para itens
            if 'itens_compra' not in st.session_state:
                st.session_state.itens_compra = []
            
            # Fornecedor
            fornecedor = st.text_input("🏪 Fornecedor", placeholder="Nome do fornecedor (opcional)")
            
            st.markdown("#### 📦 Adicionar Itens da Compra")
            
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            with col1:
                nome_item = st.text_input("Nome do Item", key="nome_item_manual", placeholder="Ex: Chocolate Meio Amargo 500g")
            with col2:
                qtd_item = st.number_input("Quantidade", min_value=0.01, value=1.0, step=0.01, key="qtd_item_manual")
            with col3:
                valor_unit_item = st.number_input("Valor Unitário (R$)", min_value=0.01, value=1.0, step=0.01, key="valor_unit_manual", format="%.2f")
            with col4:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("➕ Adicionar", key="btn_add_item_manual", use_container_width=True):
                    if nome_item:
                        item = {
                            'nome': nome_item,
                            'descricao': '',
                            'quantidade': qtd_item,
                            'valor_unitario': valor_unit_item,
                            'valor_total': qtd_item * valor_unit_item
                        }
                        st.session_state.itens_compra.append(item)
                        st.success(f"✅ Item '{nome_item}' adicionado!")
                        st.rerun()
                    else:
                        st.warning("⚠️ Digite o nome do item")
            
            # Mostrar itens adicionados
            if st.session_state.itens_compra:
                st.markdown("---")
                st.markdown("### 🛒 Itens Adicionados")
                
                total_compra = 0
                for idx, item in enumerate(st.session_state.itens_compra):
                    col1, col2, col3, col4, col5 = st.columns([3, 1, 2, 2, 1])
                    with col1:
                        st.write(f"**{item['nome']}**")
                    with col2:
                        st.write(f"{item['quantidade']:.2f} un")
                    with col3:
                        st.write(f"R$ {item['valor_unitario']:.2f}")
                    with col4:
                        st.write(f"**R$ {item['valor_total']:.2f}**")
                    with col5:
                        if st.button("🗑️", key=f"del_item_{idx}", use_container_width=True):
                            st.session_state.itens_compra.pop(idx)
                            st.rerun()
                    
                    total_compra += item['valor_total']
                
                st.markdown("---")
                st.markdown(f"### 💰 Valor Total: R$ {total_compra:,.2f}")
                
                # Opções de pagamento
                num_parcelas = st.selectbox(
                    "💳 Número de Parcelas",
                    options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                    format_func=lambda x: f"{x}x" if x > 1 else "À vista",
                    key="parcelas_manual"
                )
                
                if num_parcelas > 1:
                    valor_parcela = total_compra / num_parcelas
                    st.info(f"💰 Valor de cada parcela: R$ {valor_parcela:,.2f}")
                
                descricao_manual = st.text_area("📝 Observações (opcional)", key="obs_manual", placeholder="Informações adicionais sobre a compra...")
                
                # Botão para registrar
                if st.button("✅ Registrar Compra com Itens", type="primary", use_container_width=True, key="btn_registrar_manual"):
                    try:
                        inserir_compra_com_itens(supabase, total_compra, descricao_manual, st.session_state.itens_compra, None, num_parcelas, fornecedor)
                        parcelas_info = f"{num_parcelas}x de R$ {total_compra/num_parcelas:,.2f}" if num_parcelas > 1 else "à vista"
                        st.markdown(f"""
                            <div class='success-message'>
                                ✅ <strong>Compra registrada com sucesso!</strong><br>
                                {len(st.session_state.itens_compra)} itens cadastrados<br>
                                Valor: R$ {total_compra:,.2f} ({parcelas_info})
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Guardar itens no session state para converter em materiais
                        st.session_state.itens_importados_manual = st.session_state.itens_compra.copy()
                        st.session_state.fornecedor_manual = fornecedor
                        st.session_state.itens_compra = []
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao registrar compra: {str(e)}")
                
                # Seção para converter itens em materiais
                if 'itens_importados_manual' in st.session_state and st.session_state.itens_importados_manual:
                    st.markdown("---")
                    st.markdown("### 📦 Converter Itens em Materiais para Ficha Técnica")
                    st.info("💡 Os itens desta compra podem ser cadastrados como materiais para usar na composição das Boxes!")
                    
                    for idx, item in enumerate(st.session_state.itens_importados_manual):
                        with st.expander(f"📦 {item.get('nome', 'Produto')} - R$ {float(item.get('valor_total', 0)):,.2f}"):
                            col1, col2, col3 = st.columns([2, 1, 1])
                            
                            with col1:
                                st.write(f"**Nome original:** {item.get('nome', '')}")
                                st.write(f"**Descrição:** {item.get('descricao', '-')}")
                                
                                # Detectar quantidade no nome (ex: "50 Unidades...")
                                nome_original = item.get('nome', '')
                                qtd_embalagem = 1
                                
                                # Tentar extrair quantidade do nome APENAS para calcular custo
                                import re
                                match = re.match(r'(\d+)\s+(unidades?|un|pcs?|peças?)\s+(.+)', nome_original, re.IGNORECASE)
                                if match:
                                    qtd_embalagem = int(match.group(1))
                                    st.success(f"✨ Detectado: **{qtd_embalagem} unidades** na embalagem")
                                
                                # Permitir edição - USAR NOME ORIGINAL COMPLETO
                                nome_material = st.text_input(
                                    "Nome do Material", 
                                    value=nome_original,
                                    key=f"nome_mat_manual_{idx}"
                                )
                                
                                qtd_embalagem_edit = st.number_input(
                                    "Quantas unidades vêm na embalagem?",
                                    min_value=1,
                                    value=qtd_embalagem,
                                    help="Ex: Se comprou '50 Unidades Balão', coloque 50",
                                    key=f"qtd_emb_manual_{idx}"
                                )
                            
                            with col2:
                                qtd_comprada = float(item.get('quantidade', 1))
                                valor_total_item = float(item.get('valor_total', 0))
                                
                                st.metric("Qtd Comprada", f"{qtd_comprada:.0f}")
                                st.metric("Valor Total", f"R$ {valor_total_item:.2f}")
                                
                                # Calcular valor unitário real
                                qtd_total_unidades = qtd_comprada * qtd_embalagem_edit
                                valor_unitario_real = valor_total_item / qtd_total_unidades if qtd_total_unidades > 0 else 0
                                
                                st.metric("Total de Unidades", f"{qtd_total_unidades:.0f}")
                                st.metric("Custo/Unidade", f"R$ {valor_unitario_real:.4f}", 
                                         help="Este é o custo que será usado na Ficha Técnica")
                            
                            with col3:
                                # Detectar unidade automaticamente
                                unidade_detectada = detectar_unidade_material(nome_material)
                                unidades_opcoes = ["unidade", "metro", "centímetro", "litro", "mililitro", "kg", "grama", "pacote", "rolo"]
                                indice_inicial = unidades_opcoes.index(unidade_detectada) if unidade_detectada in unidades_opcoes else 0
                                
                                unidade_med = st.selectbox(
                                    "Unidade de Medida",
                                    unidades_opcoes,
                                    index=indice_inicial,
                                    key=f"unid_manual_{idx}",
                                    help=f"✨ Detectado: {unidade_detectada}"
                                )
                                
                                # Botão para cadastrar como material
                                if st.button(f"➕ Cadastrar como Material", key=f"btn_mat_manual_{idx}", use_container_width=True):
                                    try:
                                        # Buscar materiais existentes para verificar similaridade
                                        todos_materiais = supabase.table("singelo_materiais").select("*").execute()
                                        
                                        # Buscar similares
                                        similares = buscar_materiais_similares(nome_material, todos_materiais.data if todos_materiais.data else [])
                                        
                                        # Verificar se já existe exatamente com este nome
                                        existe_exato = supabase.table("singelo_materiais").select("*").eq("nome", nome_material).execute()
                                        
                                        if existe_exato.data:
                                            # Material com nome exato já existe - atualizar com custo médio ponderado
                                            material_existente = existe_exato.data[0]
                                            estoque_atual = float(material_existente['estoque_atual'])
                                            custo_atual = float(material_existente['custo_unitario'])
                                            
                                            # Calcular custo médio ponderado
                                            custo_medio = calcular_custo_medio_ponderado(
                                                estoque_atual, custo_atual,
                                                qtd_total_unidades, valor_unitario_real
                                            )
                                            
                                            novo_estoque = estoque_atual + qtd_total_unidades
                                            
                                            supabase.table("singelo_materiais").update({
                                                "custo_unitario": custo_medio,
                                                "estoque_atual": novo_estoque,
                                                "ultima_compra_data": datetime.now().date().isoformat(),
                                                "fornecedor_principal": st.session_state.fornecedor_manual,
                                                "updated_at": datetime.now().isoformat()
                                            }).eq("id", material_existente['id']).execute()
                                            
                                            st.success(f"""
                                            ✅ Material atualizado com **custo médio ponderado**!
                                            - Custo anterior: R$ {custo_atual:.4f}
                                            - Novo custo: R$ {valor_unitario_real:.4f}
                                            - **Custo médio: R$ {custo_medio:.4f}**
                                            - Estoque: {estoque_atual:.0f} + {qtd_total_unidades:.0f} = **{novo_estoque:.0f}**
                                            """)
                                            
                                        elif similares:
                                            # Encontrou materiais similares - perguntar se é o mesmo
                                            st.warning(f"🔍 Encontrado {len(similares)} material(is) similar(es):")
                                            
                                            col_botoes = st.columns(len(similares[:3]) + 1)
                                            
                                            for i, sim in enumerate(similares[:3]):  # Mostrar no máximo 3
                                                mat = sim['material']
                                                similaridade_pct = sim['similaridade'] * 100
                                                
                                                with col_botoes[i]:
                                                    st.markdown(f"**{mat['nome']}**")
                                                    st.caption(f"{similaridade_pct:.0f}% similar")
                                                    st.caption(f"R$ {float(mat['custo_unitario']):.4f}")
                                                    st.caption(f"{float(mat['estoque_atual']):.2f} {mat['unidade_medida']}")
                                                    
                                                    if st.button(f"🔗 Vincular", key=f"vincular_{idx}_{mat['id']}", use_container_width=True):
                                                        # Vincular a este material e atualizar com custo médio
                                                        estoque_atual = float(mat['estoque_atual'])
                                                        custo_atual = float(mat['custo_unitario'])
                                                        
                                                        custo_medio = calcular_custo_medio_ponderado(
                                                            estoque_atual, custo_atual,
                                                            qtd_total_unidades, valor_unitario_real
                                                        )
                                                        
                                                        novo_estoque = estoque_atual + qtd_total_unidades
                                                        
                                                        supabase.table("singelo_materiais").update({
                                                            "custo_unitario": custo_medio,
                                                            "estoque_atual": novo_estoque,
                                                            "ultima_compra_data": datetime.now().date().isoformat(),
                                                            "updated_at": datetime.now().isoformat()
                                                        }).eq("id", mat['id']).execute()
                                                        
                                                        st.success(f"""
                                                        ✅ Vinculado a **{mat['nome']}**!
                                                        - Custo médio: R$ {custo_medio:.4f}
                                                        - Estoque: {novo_estoque:.0f}
                                                        """)
                                                        st.rerun()
                                            
                                            with col_botoes[-1]:
                                                st.markdown("**Criar novo?**")
                                                st.caption("Material diferente")
                                                st.write("")
                                                st.write("")
                                                if st.button(f"➕ Novo", key=f"novo_{idx}", use_container_width=True):
                                                    # Criar novo material - usar descrição original da NF-e
                                                    descricao_original = item.get('descricao', '') or nome_original
                                                    material_data = {
                                                        "nome": nome_material,
                                                        "descricao": descricao_original,
                                                        "unidade_medida": unidade_med,
                                                        "estoque_atual": qtd_total_unidades,
                                                        "custo_unitario": valor_unitario_real,
                                                        "ultima_compra_data": datetime.now().date().isoformat(),
                                                        "fornecedor_principal": st.session_state.fornecedor_manual,
                                                        "observacoes": f"Cadastrado - {qtd_embalagem_edit} unidades por embalagem"
                                                    }
                                                    supabase.table("singelo_materiais").insert(material_data).execute()
                                                    st.success(f"✅ Material '{nome_material}' criado!")
                                                    st.rerun()
                                            
                                        else:
                                            # Não encontrou similares - cadastrar novo
                                            descricao_original = item.get('descricao', '') or nome_original
                                            material_data = {
                                                "nome": nome_material,
                                                "descricao": descricao_original,
                                                "unidade_medida": unidade_med,
                                                "estoque_atual": qtd_total_unidades,
                                                "custo_unitario": valor_unitario_real,
                                                "ultima_compra_data": datetime.now().date().isoformat(),
                                                "fornecedor_principal": st.session_state.fornecedor_manual,
                                                "observacoes": f"Cadastrado - {qtd_embalagem_edit} unidades por embalagem"
                                            }
                                            supabase.table("singelo_materiais").insert(material_data).execute()
                                            st.success(f"✅ Material '{nome_material}' cadastrado com sucesso!")
                                        
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Erro: {str(e)}")
                    
                    if st.button("🔄 Limpar Lista", key="limpar_itens_manual"):
                        del st.session_state.itens_importados_manual
                        del st.session_state.fornecedor_manual
                        st.rerun()
            else:
                st.info("📋 Adicione itens à compra usando o formulário acima")
        
        with tab2:
            st.markdown("### 📄 Importar Documento Fiscal XML")
            
            # Sub-tabs para NF-e e Cupom
            subtab1, subtab2 = st.tabs(["📄 NF-e (Nota Fiscal)", "🧾 Cupom Fiscal (NFC-e)"])
            
            with subtab1:
                st.info("💡 **NF-e:** Nota Fiscal Eletrônica completa. Geralmente usada em compras de fornecedores.")
                
                uploaded_nfe = st.file_uploader(
                    "Selecione o arquivo XML da NF-e",
                    type=['xml'],
                    help="Faça upload do arquivo XML da Nota Fiscal Eletrônica",
                    key="nfe_upload"
                )
                
                if uploaded_nfe is not None:
                    try:
                        xml_content = uploaded_nfe.read()
                        
                        with st.spinner("Processando NF-e..."):
                            dados = extrair_dados_xml_nfe_v2(xml_content)
                        
                        if dados['sucesso']:
                            st.success(dados['mensagem'])
                            
                            # Mostrar dados extraídos
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("💵 Valor Total", f"R$ {dados['valor_total']:,.2f}")
                            with col2:
                                st.metric("📅 Data", dados['data'].strftime('%d/%m/%Y'))
                            with col3:
                                st.metric("🏪 Fornecedor", dados.get('fornecedor', 'N/A'))
                            
                            # Mostrar itens
                            if dados.get('itens'):
                                st.markdown("### 🛒 Produtos da NF-e")
                                st.markdown(f"**Total de itens:** {len(dados['itens'])}")
                                
                                import pandas as pd
                                df_itens = pd.DataFrame(dados['itens'])
                                df_itens['Quantidade'] = df_itens['quantidade'].apply(lambda x: f"{x:.2f}")
                                df_itens['Valor Unit.'] = df_itens['valor_unitario'].apply(lambda x: f"R$ {x:.2f}")
                                df_itens['Valor Total'] = df_itens['valor_total'].apply(lambda x: f"R$ {x:.2f}")
                                df_itens = df_itens[['nome', 'descricao', 'Quantidade', 'Valor Unit.', 'Valor Total']]
                                df_itens.columns = ['Produto', 'Descrição', 'Quantidade', 'Valor Unit.', 'Valor Total']
                                
                                st.dataframe(df_itens, use_container_width=True, hide_index=True)
                            
                            st.markdown("---")
                            
                            # Perguntar se gera contas a pagar
                            st.markdown("### 💳 Forma de Pagamento")
                            gerar_parcelas = st.radio(
                                "Esta compra vai para o Contas a Pagar?",
                                ["Sim, gerar parcelas no cartão de crédito", "Não, foi pago à vista (dinheiro/PIX/outro)"],
                                key="gerar_parcelas_nfe",
                                help="Escolha 'Sim' se for parcelado no cartão de crédito. Escolha 'Não' se já foi pago."
                            )
                            
                            num_parcelas_nfe = 1
                            if gerar_parcelas == "Sim, gerar parcelas no cartão de crédito":
                                # Opções de pagamento
                                num_parcelas_nfe = st.selectbox(
                                    "💳 Número de Parcelas",
                                    options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                                    format_func=lambda x: f"{x}x" if x > 1 else "À vista",
                                    key="parcelas_nfe"
                                )
                                
                                if num_parcelas_nfe > 1:
                                    st.info(f"💰 Valor de cada parcela: R$ {dados['valor_total']/num_parcelas_nfe:,.2f}")
                            else:
                                st.info("ℹ️ A compra será registrada sem gerar parcelas no contas a pagar.")
                            
                            # Botão confirmar
                            if st.button("✅ Confirmar e Registrar NF-e", type="primary", use_container_width=True, key="btn_confirmar_nfe"):
                                try:
                                    descricao_nfe = f"NF-e - {dados.get('fornecedor', 'Fornecedor não identificado')}"
                                    
                                    # Se não gerar parcelas, passa 0 para num_parcelas
                                    parcelas_final = num_parcelas_nfe if gerar_parcelas == "Sim, gerar parcelas no cartão de crédito" else 0
                                    
                                    inserir_compra_com_itens(supabase, dados['valor_total'], descricao_nfe, dados.get('itens', []), dados['data'], parcelas_final, dados.get('fornecedor', ''))
                                    
                                    msg_parcelas = f"{parcelas_final}x no cartão de crédito" if parcelas_final > 0 else "Pago à vista (sem parcelas)"
                                    st.markdown(f"""
                                        <div class='success-message'>
                                            ✅ <strong>NF-e importada com sucesso!</strong><br>
                                            Fornecedor: {dados.get('fornecedor', 'N/A')}<br>
                                            {len(dados.get('itens', []))} produtos cadastrados<br>
                                            Valor: R$ {dados['valor_total']:,.2f}<br>
                                            Pagamento: {msg_parcelas}
                                        </div>
                                    """, unsafe_allow_html=True)
                                    st.balloons()
                                    
                                    # Guardar itens no session state para converter em materiais
                                    st.session_state.itens_importados_nfe = dados.get('itens', [])
                                    st.session_state.fornecedor_nfe = dados.get('fornecedor', '')
                                    
                                except Exception as e:
                                    st.error(f"❌ Erro ao registrar: {str(e)}")
                            
                            # Seção para converter itens em materiais
                            if 'itens_importados_nfe' in st.session_state and st.session_state.itens_importados_nfe:
                                st.markdown("---")
                                st.markdown("### 📦 Converter Itens em Materiais para Ficha Técnica")
                                st.info("💡 Os itens desta NF-e podem ser cadastrados como materiais para usar na composição das Boxes!")
                                
                                for idx, item in enumerate(st.session_state.itens_importados_nfe):
                                    with st.expander(f"📦 {item.get('nome', 'Produto')} - R$ {float(item.get('valor_total', 0)):,.2f}"):
                                        col1, col2, col3 = st.columns([2, 1, 1])
                                        
                                        with col1:
                                            st.write(f"**Nome original:** {item.get('nome', '')}")
                                            st.write(f"**Descrição:** {item.get('descricao', '-')}")
                                            
                                            # Detectar quantidade no nome (ex: "50 Unidades...")
                                            nome_original = item.get('nome', '')
                                            qtd_embalagem = 1
                                            
                                            # Tentar extrair quantidade do nome APENAS para calcular custo
                                            import re
                                            match = re.match(r'(\d+)\s+(unidades?|un|pcs?|peças?)\s+(.+)', nome_original, re.IGNORECASE)
                                            if match:
                                                qtd_embalagem = int(match.group(1))
                                                st.success(f"✨ Detectado: **{qtd_embalagem} unidades** na embalagem")
                                            
                                            # Permitir edição - USAR NOME ORIGINAL COMPLETO
                                            nome_material = st.text_input(
                                                "Nome do Material", 
                                                value=nome_original,
                                                key=f"nome_mat_{idx}"
                                            )
                                            
                                            qtd_embalagem_edit = st.number_input(
                                                "Quantas unidades vêm na embalagem?",
                                                min_value=1,
                                                value=qtd_embalagem,
                                                help="Ex: Se comprou '50 Unidades Balão', coloque 50",
                                                key=f"qtd_emb_{idx}"
                                            )
                                        
                                        with col2:
                                            qtd_comprada = float(item.get('quantidade', 1))
                                            valor_total_item = float(item.get('valor_total', 0))
                                            
                                            st.metric("Qtd Comprada", f"{qtd_comprada:.0f}")
                                            st.metric("Valor Total", f"R$ {valor_total_item:.2f}")
                                            
                                            # Calcular valor unitário real
                                            qtd_total_unidades = qtd_comprada * qtd_embalagem_edit
                                            valor_unitario_real = valor_total_item / qtd_total_unidades if qtd_total_unidades > 0 else 0
                                            
                                            st.metric("Total de Unidades", f"{qtd_total_unidades:.0f}")
                                            st.metric("Custo/Unidade", f"R$ {valor_unitario_real:.4f}", 
                                                     help="Este é o custo que será usado na Ficha Técnica")
                                        
                                        with col3:
                                            # Detectar unidade automaticamente
                                            unidade_detectada = detectar_unidade_material(nome_material)
                                            unidades_opcoes = ["unidade", "metro", "centímetro", "litro", "mililitro", "kg", "grama", "pacote", "rolo"]
                                            indice_inicial = unidades_opcoes.index(unidade_detectada) if unidade_detectada in unidades_opcoes else 0
                                            
                                            unidade_med = st.selectbox(
                                                "Unidade de Medida",
                                                unidades_opcoes,
                                                index=indice_inicial,
                                                key=f"unid_{idx}",
                                                help=f"✨ Detectado: {unidade_detectada}"
                                            )
                                            
                                            # Botão para cadastrar como material
                                            if st.button(f"➕ Cadastrar como Material", key=f"btn_mat_{idx}", use_container_width=True):
                                                try:
                                                    # Verificar se já existe
                                                    existe = supabase.table("singelo_materiais").select("id, custo_unitario").eq("nome", nome_material).execute()
                                                    
                                                    if existe.data:
                                                        # Atualizar custo
                                                        material_id = existe.data[0]['id']
                                                        custo_antigo = float(existe.data[0]['custo_unitario'])
                                                        
                                                        supabase.table("singelo_materiais").update({
                                                            "custo_unitario": valor_unitario_real,
                                                            "ultima_compra_data": datetime.now().date().isoformat(),
                                                            "fornecedor_principal": st.session_state.fornecedor_nfe,
                                                            "estoque_atual": qtd_total_unidades,  # Adicionar ao estoque
                                                            "updated_at": datetime.now().isoformat()
                                                        }).eq("id", material_id).execute()
                                                        
                                                        st.success(f"✅ Material atualizado! Custo: R$ {custo_antigo:.4f} → R$ {valor_unitario_real:.4f}")
                                                    else:
                                                        # Cadastrar novo - usar descrição original da NF-e
                                                        nome_original = item.get('nome', '')
                                                        descricao_original = item.get('descricao', '') or nome_original
                                                        material_data = {
                                                            "nome": nome_material,
                                                            "descricao": descricao_original,
                                                            "unidade_medida": unidade_med,
                                                            "estoque_atual": qtd_total_unidades,
                                                            "custo_unitario": valor_unitario_real,
                                                            "ultima_compra_data": datetime.now().date().isoformat(),
                                                            "fornecedor_principal": st.session_state.fornecedor_nfe,
                                                            "observacoes": f"Importado de NF-e - {qtd_embalagem_edit} unidades por embalagem"
                                                        }
                                                        supabase.table("singelo_materiais").insert(material_data).execute()
                                                        st.success(f"✅ Material '{nome_material}' cadastrado com sucesso!")
                                                    
                                                    st.rerun()
                                                except Exception as e:
                                                    st.error(f"Erro: {str(e)}")
                                
                                if st.button("🔄 Limpar Lista", key="limpar_itens_nfe"):
                                    del st.session_state.itens_importados_nfe
                                    del st.session_state.fornecedor_nfe
                                    st.rerun()
                        
                        else:
                            st.error(dados['mensagem'])
                    except Exception as e:
                        st.error(f"❌ Erro ao processar NF-e: {str(e)}")
            
            with subtab2:
                st.info("💡 **Cupom Fiscal:** Nota fiscal simplificada. Escaneie o QR Code do cupom para obter o XML.")
                
                uploaded_cupom = st.file_uploader(
                    "Selecione o arquivo XML do Cupom",
                    type=['xml'],
                    help="Faça upload do arquivo XML obtido via QR Code",
                    key="cupom_upload"
                )
                
                if uploaded_cupom is not None:
                    try:
                        xml_content = uploaded_cupom.read()
                        content_str = xml_content.decode('utf-8', errors='ignore') if isinstance(xml_content, bytes) else xml_content
                        
                        with st.spinner("Processando Cupom Fiscal..."):
                            if '<!DOCTYPE html>' in content_str or '<html' in content_str:
                                dados = extrair_dados_html_nfce(xml_content)
                            else:
                                dados = extrair_dados_xml_nfe(xml_content)
                        
                        if dados['sucesso']:
                            st.success(dados['mensagem'])
                            
                            # Mostrar dados
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("💵 Valor Total", f"R$ {dados['valor_total']:,.2f}")
                            with col2:
                                st.metric("📅 Data", dados['data'].strftime('%d/%m/%Y'))
                            
                            # Mostrar itens se houver
                            if dados.get('itens'):
                                st.markdown("### 🛒 Itens do Cupom")
                                st.markdown(f"**Total de itens:** {len(dados['itens'])}")
                                
                                import pandas as pd
                                df_itens = pd.DataFrame(dados['itens'])
                                df_itens['Quantidade'] = df_itens['quantidade'].apply(lambda x: f"{x:.2f}")
                                df_itens['Valor Unit.'] = df_itens['valor_unitario'].apply(lambda x: f"R$ {x:.2f}")
                                df_itens['Valor Total'] = df_itens['valor_total'].apply(lambda x: f"R$ {x:.2f}")
                                df_itens = df_itens[['nome', 'Quantidade', 'Valor Unit.', 'Valor Total']]
                                df_itens.columns = ['Produto', 'Quantidade', 'Valor Unit.', 'Valor Total']
                                
                                st.dataframe(df_itens, use_container_width=True, hide_index=True)
                            
                            st.markdown("---")
                            
                            # Opções de pagamento
                            num_parcelas_cupom = st.selectbox(
                                "💳 Número de Parcelas",
                                options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                                format_func=lambda x: f"{x}x" if x > 1 else "À vista",
                                key="parcelas_cupom"
                            )
                            
                            if num_parcelas_cupom > 1:
                                st.info(f"💰 Valor de cada parcela: R$ {dados['valor_total']/num_parcelas_cupom:,.2f}")
                            
                            # Botão confirmar
                            if st.button("✅ Confirmar e Registrar Cupom", type="primary", use_container_width=True, key="btn_confirmar_cupom"):
                                try:
                                    descricao_cupom = f"Cupom Fiscal - {dados.get('descricao', 'Compra')}"
                                    inserir_compra_com_itens(supabase, dados['valor_total'], descricao_cupom, dados.get('itens', []), dados['data'], num_parcelas_cupom, "")
                                    st.markdown(f"""
                                        <div class='success-message'>
                                            ✅ <strong>Cupom importado com sucesso!</strong><br>
                                            {len(dados.get('itens', []))} itens cadastrados<br>
                                            Valor: R$ {dados['valor_total']:,.2f}
                                        </div>
                                    """, unsafe_allow_html=True)
                                    st.balloons()
                                    
                                    # Guardar itens no session state para converter em materiais
                                    st.session_state.itens_importados_cupom = dados.get('itens', [])
                                    st.session_state.fornecedor_cupom = dados.get('fornecedor', 'Cupom Fiscal')
                                    
                                except Exception as e:
                                    st.error(f"❌ Erro ao registrar: {str(e)}")
                            
                            # Seção para converter itens em materiais
                            if 'itens_importados_cupom' in st.session_state and st.session_state.itens_importados_cupom:
                                st.markdown("---")
                                st.markdown("### 📦 Converter Itens em Materiais para Ficha Técnica")
                                st.info("💡 Os itens deste cupom podem ser cadastrados como materiais para usar na composição das Boxes!")
                                
                                for idx, item in enumerate(st.session_state.itens_importados_cupom):
                                    with st.expander(f"📦 {item.get('nome', 'Produto')} - R$ {float(item.get('valor_total', 0)):,.2f}"):
                                        col1, col2, col3 = st.columns([2, 1, 1])
                                        
                                        with col1:
                                            st.write(f"**Nome original:** {item.get('nome', '')}")
                                            st.write(f"**Descrição:** {item.get('descricao', '-')}")
                                            
                                            # Detectar quantidade no nome (ex: "50 Unidades...")
                                            nome_original = item.get('nome', '')
                                            qtd_embalagem = 1
                                            
                                            # Tentar extrair quantidade do nome APENAS para calcular custo
                                            import re
                                            match = re.match(r'(\d+)\s+(unidades?|un|pcs?|peças?)\s+(.+)', nome_original, re.IGNORECASE)
                                            if match:
                                                qtd_embalagem = int(match.group(1))
                                                st.success(f"✨ Detectado: **{qtd_embalagem} unidades** na embalagem")
                                            
                                            # Permitir edição - USAR NOME ORIGINAL COMPLETO
                                            nome_material = st.text_input(
                                                "Nome do Material", 
                                                value=nome_original,
                                                key=f"nome_mat_cupom_{idx}"
                                            )
                                            
                                            qtd_embalagem_edit = st.number_input(
                                                "Quantas unidades vêm na embalagem?",
                                                min_value=1,
                                                value=qtd_embalagem,
                                                help="Ex: Se comprou '50 Unidades Balão', coloque 50",
                                                key=f"qtd_emb_cupom_{idx}"
                                            )
                                        
                                        with col2:
                                            qtd_comprada = float(item.get('quantidade', 1))
                                            valor_total_item = float(item.get('valor_total', 0))
                                            
                                            st.metric("Qtd Comprada", f"{qtd_comprada:.0f}")
                                            st.metric("Valor Total", f"R$ {valor_total_item:.2f}")
                                            
                                            # Calcular valor unitário real
                                            qtd_total_unidades = qtd_comprada * qtd_embalagem_edit
                                            valor_unitario_real = valor_total_item / qtd_total_unidades if qtd_total_unidades > 0 else 0
                                            
                                            st.metric("Total de Unidades", f"{qtd_total_unidades:.0f}")
                                            st.metric("Custo/Unidade", f"R$ {valor_unitario_real:.4f}", 
                                                     help="Este é o custo que será usado na Ficha Técnica")
                                        
                                        with col3:
                                            # Detectar unidade automaticamente
                                            unidade_detectada = detectar_unidade_material(nome_material)
                                            unidades_opcoes = ["unidade", "metro", "centímetro", "litro", "mililitro", "kg", "grama", "pacote", "rolo"]
                                            indice_inicial = unidades_opcoes.index(unidade_detectada) if unidade_detectada in unidades_opcoes else 0
                                            
                                            unidade_med = st.selectbox(
                                                "Unidade de Medida",
                                                unidades_opcoes,
                                                index=indice_inicial,
                                                key=f"unid_cupom_{idx}",
                                                help=f"✨ Detectado: {unidade_detectada}"
                                            )
                                            
                                            # Botão para cadastrar como material
                                            if st.button(f"➕ Cadastrar como Material", key=f"btn_mat_cupom_{idx}", use_container_width=True):
                                                try:
                                                    # Verificar se já existe
                                                    existe = supabase.table("singelo_materiais").select("id, custo_unitario").eq("nome", nome_material).execute()
                                                    
                                                    if existe.data:
                                                        # Atualizar custo
                                                        material_id = existe.data[0]['id']
                                                        custo_antigo = float(existe.data[0]['custo_unitario'])
                                                        
                                                        supabase.table("singelo_materiais").update({
                                                            "custo_unitario": valor_unitario_real,
                                                            "ultima_compra_data": datetime.now().date().isoformat(),
                                                            "fornecedor_principal": st.session_state.fornecedor_cupom,
                                                            "estoque_atual": qtd_total_unidades,
                                                            "updated_at": datetime.now().isoformat()
                                                        }).eq("id", material_id).execute()
                                                        
                                                        st.success(f"✅ Material atualizado! Custo: R$ {custo_antigo:.4f} → R$ {valor_unitario_real:.4f}")
                                                    else:
                                                        # Cadastrar novo - usar descrição original do Cupom
                                                        nome_original = item.get('nome', '')
                                                        descricao_original = item.get('descricao', '') or nome_original
                                                        material_data = {
                                                            "nome": nome_material,
                                                            "descricao": descricao_original,
                                                            "unidade_medida": unidade_med,
                                                            "estoque_atual": qtd_total_unidades,
                                                            "custo_unitario": valor_unitario_real,
                                                            "ultima_compra_data": datetime.now().date().isoformat(),
                                                            "fornecedor_principal": st.session_state.fornecedor_cupom,
                                                            "observacoes": f"Importado de Cupom Fiscal - {qtd_embalagem_edit} unidades por embalagem"
                                                        }
                                                        supabase.table("singelo_materiais").insert(material_data).execute()
                                                        st.success(f"✅ Material '{nome_material}' cadastrado com sucesso!")
                                                    
                                                    st.rerun()
                                                except Exception as e:
                                                    st.error(f"Erro: {str(e)}")
                                
                                if st.button("🔄 Limpar Lista", key="limpar_itens_cupom"):
                                    del st.session_state.itens_importados_cupom
                                    del st.session_state.fornecedor_cupom
                                    st.rerun()
                        else:
                            st.error(dados['mensagem'])
                    except Exception as e:
                        st.error(f"❌ Erro ao processar cupom: {str(e)}")
        
        with tab3:
            st.markdown("### 🔑 Buscar e Importar NF-e")
            st.info("💡 Digite ou cole a chave de 44 dígitos - tentaremos buscar automaticamente da SEFAZ")
            
            # Campo para digitar ou colar a chave
            chave_acesso = st.text_input(
                "Chave de Acesso (44 dígitos)",
                placeholder="Ex: 35240112345678901234550010000123451234567890",
                help="Digite ou cole a chave - pode conter espaços que serão removidos automaticamente",
                key="chave_acesso_input"
            )
            
            # Botão para buscar
            if st.button("🔍 Buscar e Importar da SEFAZ", use_container_width=True, type="primary", key="btn_buscar_chave"):
                if chave_acesso:
                    # Remover espaços e caracteres não numéricos
                    chave_limpa = ''.join(filter(str.isdigit, chave_acesso))
                    
                    if len(chave_limpa) != 44:
                        st.error("⚠️ A chave deve ter exatamente 44 dígitos")
                    else:
                        with st.spinner("🌐 Conectando com a SEFAZ..."):
                            # Tentar baixar automaticamente
                            import requests
                            
                            # Extrair UF da chave
                            uf_codigo = chave_limpa[:2]
                            uf_map = {
                                '35': 'SP', '33': 'RJ', '31': 'MG', '41': 'PR', '42': 'SC', '43': 'RS',
                                '53': 'DF', '52': 'GO', '51': 'MT', '50': 'MS', '11': 'RO', '12': 'AC',
                                '13': 'AM', '14': 'RR', '15': 'PA', '16': 'AP', '17': 'TO', '21': 'MA',
                                '22': 'PI', '23': 'CE', '24': 'RN', '25': 'PB', '26': 'PE', '27': 'AL',
                                '28': 'SE', '29': 'BA', '32': 'ES'
                            }
                            uf = uf_map.get(uf_codigo, 'Desconhecido')
                            
                            xml_downloaded = False
                            xml_content = None
                            
                            # Tentar baixar diretamente da SEFAZ
                            try:
                                url_download = f"https://www.nfe.fazenda.gov.br/portal/consultaRecaptcha.aspx?tipoConsulta=completa&tipoConteudo=XbSeqxE8pl8=&nfe={chave_limpa}"
                                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                                response = requests.get(url_download, headers=headers, timeout=10)
                                
                                if response.status_code == 200 and '<?xml' in response.text:
                                    xml_content = response.content
                                    xml_downloaded = True
                            except:
                                pass
                            
                            # Se conseguiu baixar, processar
                            if xml_downloaded and xml_content:
                                try:
                                    dados = extrair_dados_xml_nfe(xml_content)
                                    
                                    if dados['sucesso']:
                                        st.success("✅ XML importado automaticamente da SEFAZ!")
                                        
                                        # Mostrar dados
                                        col1, col2, col3 = st.columns(3)
                                        with col1:
                                            st.metric("💵 Valor", f"R$ {dados['valor_total']:,.2f}")
                                        with col2:
                                            st.metric("📅 Data", dados['data'].strftime('%d/%m/%Y'))
                                        with col3:
                                            st.metric("🏪 Fornecedor", dados.get('fornecedor', 'N/A'))
                                        
                                        # Mostrar itens
                                        if dados.get('itens'):
                                            st.markdown("### 🛒 Produtos")
                                            import pandas as pd
                                            df = pd.DataFrame(dados['itens'])
                                            df['Qtd'] = df['quantidade'].apply(lambda x: f"{x:.2f}")
                                            df['Unit'] = df['valor_unitario'].apply(lambda x: f"R$ {x:.2f}")
                                            df['Total'] = df['valor_total'].apply(lambda x: f"R$ {x:.2f}")
                                            st.dataframe(df[['nome', 'descricao', 'Qtd', 'Unit', 'Total']], use_container_width=True, hide_index=True)
                                        
                                        st.markdown("---")
                                        num_parcelas = st.selectbox("💳 Parcelas", [1,2,3,4,5,6,7,8,9,10,11,12], 
                                                                   format_func=lambda x: f"{x}x" if x>1 else "À vista", key="parcelas_sefaz")
                                        if num_parcelas > 1:
                                            st.info(f"💰 {num_parcelas}x de R$ {dados['valor_total']/num_parcelas:,.2f}")
                                        
                                        if st.button("✅ Confirmar e Registrar", type="primary", use_container_width=True, key="btn_confirmar_sefaz"):
                                            try:
                                                desc = f"NF-e - {dados.get('fornecedor', 'Fornecedor')}"
                                                inserir_compra_com_itens(supabase, dados['valor_total'], desc, dados.get('itens', []), 
                                                                       dados['data'], num_parcelas, dados.get('fornecedor', ''))
                                                st.success("✅ NF-e registrada com sucesso!")
                                                st.balloons()
                                            except Exception as e:
                                                st.error(f"❌ Erro: {str(e)}")
                                    else:
                                        raise Exception(dados['mensagem'])
                                except:
                                    xml_downloaded = False
                            
                            # Se não baixou automaticamente
                            if not xml_downloaded:
                                resultado = buscar_xml_por_chave(chave_limpa)
                                
                                st.warning("⚠️ Download automático não disponível")
                                st.markdown(f"**Estado:** {uf} | **Chave:** `{chave_limpa}`")
                                
                                # Botão para copiar a chave
                                st.code(chave_limpa, language=None)
                                
                                st.markdown("---")
                                st.markdown("### 📥 Como baixar o XML:")
                                
                                # Opção principal: Meu Danfe
                                st.info("💡 **Recomendado:** Use o site Meu Danfe para baixar o XML gratuitamente!")
                                
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    st.markdown("""
                                    **Passo a passo:**
                                    1. 🔗 Clique no botão ao lado para abrir o Meu Danfe
                                    2. Cole a chave de acesso no campo indicado
                                    3. Clique em **BUSCAR**
                                    4. Baixe o **XML** da nota fiscal
                                    5. Volte aqui e use a aba **"📄 Importar Documento"** para fazer upload
                                    """)
                                with col2:
                                    st.markdown("")
                                    st.markdown("")
                                    st.link_button("🌐 Abrir Meu Danfe", "https://meudanfe.com.br/#", type="primary", use_container_width=True)
                                
                                # Opção alternativa: SEFAZ
                                with st.expander("🔄 Opção alternativa: SEFAZ"):
                                    if resultado.get('sucesso') and resultado.get('url'):
                                        st.markdown(f"""
                                        1. 🔗 **[Acesse a SEFAZ-{uf}]({resultado['url']})**
                                        2. Cole a chave: `{chave_limpa}`
                                        3. Baixe o XML
                                        4. Use a aba **"Importar Documento"** para fazer upload
                                        """)
                                    else:
                                        st.markdown(f"""
                                        - Acesse o site da SEFAZ-{uf}
                                        - Cole a chave: `{chave_limpa}`
                                        - Baixe o XML e use "Importar Documento"
                                        - **Ou escaneie o QR Code** do cupom para acesso rápido
                                        """)
                                
                                # Opção de colar XML
                                with st.expander("📄 Ou cole o conteúdo do XML aqui"):
                                    xml_colado = st.text_area("Cole o XML:", height=120, placeholder='<?xml version="1.0"?>', key="xml_fallback")
                                    if st.button("🔄 Processar", key="btn_fallback"):
                                        if xml_colado and len(xml_colado) > 100:
                                            try:
                                                dados = extrair_dados_xml_nfe(xml_colado.encode('utf-8'))
                                                if dados['sucesso']:
                                                    st.success("✅ Processado!")
                                                    col1, col2 = st.columns(2)
                                                    with col1:
                                                        st.metric("💵", f"R$ {dados['valor_total']:,.2f}")
                                                    with col2:
                                                        st.metric("🏪", dados.get('fornecedor', 'N/A'))
                                                    
                                                    if dados.get('itens'):
                                                        import pandas as pd
                                                        df = pd.DataFrame(dados['itens'])
                                                        st.dataframe(df[['nome', 'quantidade', 'valor_total']], hide_index=True)
                                                    
                                                    num_p = st.selectbox("💳 Parcelas", [1,2,3,4,5,6,7,8,9,10,11,12], 
                                                                        format_func=lambda x: f"{x}x" if x>1 else "À vista", key="parc_fb")
                                                    if st.button("✅ Registrar", type="primary", key="btn_reg_fb"):
                                                        try:
                                                            desc = f"NF-e - {dados.get('fornecedor', 'Fornecedor')}"
                                                            inserir_compra_com_itens(supabase, dados['valor_total'], desc, dados.get('itens', []), 
                                                                                   dados['data'], num_p, dados.get('fornecedor', ''))
                                                            st.success("✅ Registrado!")
                                                            st.balloons()
                                                        except Exception as e:
                                                            st.error(f"❌ {str(e)}")
                                                else:
                                                    st.error(dados['mensagem'])
                                            except Exception as e:
                                                st.error(f"❌ {str(e)}")
                                        else:
                                            st.warning("⚠️ Cole o XML completo")
                else:
                    st.warning("⚠️ Digite a chave de 44 dígitos")
    
    # ==================== LANÇAR VENDA ====================
    elif opcao == "💰 Lançar Venda":
        st.markdown("## 💰 Lançar Nova Venda")
        
        # Seletores fora do form para atualização em tempo real
        col1, col2 = st.columns(2)
        
        with col1:
            produto = st.selectbox(
                "🎁 Selecione a Box",
                options=BOXES,
                index=0,
                key="produto_select"
            )
        
        with col2:
            tamanho = st.selectbox(
                "📏 Tamanho da Box",
                options=list(TAMANHOS.keys()),
                index=0,
                help="O custo será registrado automaticamente",
                key="tamanho_select"
            )
        
        # Mostrar o custo que será registrado (atualiza em tempo real)
        custo_box = TAMANHOS[tamanho]
        st.info(f"💰 Custo desta box: R$ {custo_box:,.2f} (será registrado automaticamente nas compras)")
        
        st.markdown("### Informações da Venda")
        
        # Campos fora do form para evitar problema do Enter
        col1, col2, col3 = st.columns(3)
        
        with col1:
            quantidade = st.number_input(
                "📦 Quantidade",
                min_value=0,
                value=1,
                step=1,
                key="qtd_venda"
            )
        
        with col2:
            valor = st.number_input(
                "💵 Valor Total da Venda (R$)",
                min_value=0.00,
                value=0.00,
                step=0.01,
                format="%.2f",
                key="valor_venda"
            )
        
        with col3:
            taxa_entrega = st.number_input(
                "🚚 Taxa Entrega (R$)",
                min_value=0.00,
                value=0.00,
                step=0.01,
                format="%.2f",
                help="Valor cobrado do cliente pela entrega",
                key="taxa_entrega"
            )
        
        st.markdown("---")
        st.markdown("### 📍 Endereço de Entrega")
        
        # Inicializar session_state para endereço se não existir
        if 'endereco_logradouro' not in st.session_state:
            st.session_state.endereco_logradouro = ''
        if 'endereco_bairro' not in st.session_state:
            st.session_state.endereco_bairro = ''
        if 'endereco_cidade' not in st.session_state:
            st.session_state.endereco_cidade = ''
        if 'endereco_uf' not in st.session_state:
            st.session_state.endereco_uf = ''
        if 'ultimo_cep' not in st.session_state:
            st.session_state.ultimo_cep = ''
        
        # Campo de data de entrega
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            data_entrega = st.date_input(
                "📅 Data de Entrega",
                value=datetime.now().date(),
                help="Data prevista para entrega",
                format="DD/MM/YYYY",
                key="data_entrega"
            )
        
        with col2:
            cep_input = st.text_input(
                "📮 CEP",
                max_chars=9,
                placeholder="00000-000",
                help="Digite o CEP (8 dígitos)",
                key="cep_input"
            )
        
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            buscar_cep_btn = st.button("🔍 Buscar", use_container_width=True, key="btn_buscar_cep")
        
        # Buscar CEP quando clicar no botão
        if buscar_cep_btn:
            cep_limpo = ''.join(filter(str.isdigit, cep_input))
            if cep_limpo and len(cep_limpo) == 8:
                with st.spinner("🔍 Buscando endereço..."):
                    endereco_encontrado = buscar_cep(cep_input)
                    if endereco_encontrado['sucesso']:
                        # Atualizar session_state com os dados encontrados
                        st.session_state.endereco_logradouro = endereco_encontrado.get('logradouro', '')
                        st.session_state.endereco_bairro = endereco_encontrado.get('bairro', '')
                        st.session_state.endereco_cidade = endereco_encontrado.get('cidade', '')
                        st.session_state.endereco_uf = endereco_encontrado.get('uf', '')
                        st.session_state.ultimo_cep = cep_limpo
                        st.success(f"✅ Endereço encontrado: {endereco_encontrado['logradouro']}, {endereco_encontrado['bairro']} - {endereco_encontrado['cidade']}/{endereco_encontrado['uf']}")
                        st.rerun()
                    else:
                        st.error(f"❌ {endereco_encontrado['mensagem']}")
            else:
                st.warning("⚠️ Digite um CEP válido com 8 dígitos")
        
        # Campos de endereço (editáveis, preenchidos automaticamente)
        col1, col2 = st.columns([3, 1])
        
        with col1:
            logradouro = st.text_input(
                "🏠 Rua/Avenida",
                value=st.session_state.endereco_logradouro,
                placeholder="Ex: Rua das Flores"
            )
            # Atualizar session_state se usuário editou
            if logradouro != st.session_state.endereco_logradouro:
                st.session_state.endereco_logradouro = logradouro
        
        with col2:
            numero = st.text_input(
                "🔢 Número",
                placeholder="123",
                key="numero"
            )
        
        col1, col2 = st.columns(2)
        
        with col1:
            bairro = st.text_input(
                "🏘️ Bairro",
                value=st.session_state.endereco_bairro,
                placeholder="Ex: Centro"
            )
            # Atualizar session_state se usuário editou
            if bairro != st.session_state.endereco_bairro:
                st.session_state.endereco_bairro = bairro
        
        with col2:
            complemento = st.text_input(
                "🏢 Complemento (opcional)",
                placeholder="Ex: Apto 101, Bloco B",
                key="complemento"
            )
        
        col1, col2 = st.columns(2)
        
        with col1:
            cidade = st.text_input(
                "🌆 Cidade",
                value=st.session_state.endereco_cidade,
                placeholder="Ex: São Paulo"
            )
            # Atualizar session_state se usuário editou
            if cidade != st.session_state.endereco_cidade:
                st.session_state.endereco_cidade = cidade
        
        with col2:
            uf = st.text_input(
                "🗺️ Estado (UF)",
                value=st.session_state.endereco_uf,
                max_chars=2,
                placeholder="SP"
            )
            # Atualizar session_state se usuário editou
            if uf != st.session_state.endereco_uf:
                st.session_state.endereco_uf = uf
        
        st.markdown("---")
        
        # Botão de submit fora do form
        if st.button("✅ Registrar Venda", use_container_width=True, type="primary", key="btn_submit_venda"):
            submitted = True
        else:
            submitted = False
        
        if submitted:
            if valor <= 0:
                st.error("❌ O valor da venda deve ser maior que zero!")
            elif quantidade <= 0:
                st.error("❌ A quantidade deve ser maior que zero!")
            else:
                try:
                    # Registrar a venda com endereço
                    inserir_venda(supabase, produto, quantidade, valor, taxa_entrega, tamanho, 
                                data_entrega, cep_input, logradouro, numero, complemento, bairro, cidade, uf)
                    
                    # Registrar o custo da box automaticamente nas compras
                    custo_total = custo_box * quantidade
                    descricao_compra = f"Custo automático: {quantidade}x {tamanho} - {produto}"
                    inserir_compra(supabase, custo_total, descricao_compra)
                    
                    endereco_completo = f"{logradouro}, {numero}" if numero else logradouro
                    if complemento:
                        endereco_completo += f" - {complemento}"
                    endereco_completo += f" - {bairro}, {cidade}/{uf}" if cidade else ""
                    
                    st.markdown(f"""
                        <div class='success-message'>
                            ✅ <strong>Venda registrada com sucesso!</strong><br>
                            {produto} ({tamanho}) - {quantidade} unidade(s)<br>
                            Valor Venda: R$ {valor:,.2f}<br>
                            Taxa Entrega: R$ {taxa_entrega:,.2f}<br>
                            📅 Entrega: {data_entrega.strftime('%d/%m/%Y')}<br>
                            📍 Endereço: {endereco_completo}<br>
                            💰 Custo registrado: R$ {custo_total:,.2f}
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Limpar session_state do endereço para nova venda
                    st.session_state.endereco_logradouro = ''
                    st.session_state.endereco_bairro = ''
                    st.session_state.endereco_cidade = ''
                    st.session_state.endereco_uf = ''
                    st.session_state.ultimo_cep = ''
                    
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Erro ao registrar venda: {str(e)}")
    
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
    
    # ==================== CONTAS A PAGAR ====================
    elif opcao == "💳 Contas a Pagar":
        st.markdown("## 💳 Controle de Contas a Pagar")
        
        # Filtros de período
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            data_inicio = st.date_input(
                "📅 Data Início",
                value=datetime.now().replace(day=1),
                format="DD/MM/YYYY",
                help="Selecione a data inicial do período"
            )
        
        with col2:
            # Último dia do mês atual
            from calendar import monthrange
            ultimo_dia = monthrange(datetime.now().year, datetime.now().month)[1]
            data_fim = st.date_input(
                "📅 Data Fim",
                value=datetime.now().replace(day=ultimo_dia),
                format="DD/MM/YYYY",
                help="Selecione a data final do período"
            )
        
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔍 Filtrar", use_container_width=True):
                st.rerun()
        
        st.markdown("---")
        
        # Buscar parcelas do período
        parcelas = buscar_parcelas_pendentes(supabase, datetime.combine(data_inicio, datetime.min.time()), datetime.combine(data_fim, datetime.max.time()))
        
        # Marcar automaticamente como paga as parcelas vencidas (compras de cartão)
        parcelas_marcadas = 0
        if parcelas:
            for parcela in parcelas:
                if parcela['status'] == 'pendente':
                    data_venc = datetime.fromisoformat(parcela['data_vencimento'].replace('Z', '+00:00'))
                    # Se vencimento já passou, marcar como paga automaticamente
                    if data_venc.date() < datetime.now().date():
                        try:
                            marcar_parcela_paga(supabase, parcela['id'])
                            parcelas_marcadas += 1
                        except:
                            pass
            
            # Se marcou alguma parcela, recarregar dados
            if parcelas_marcadas > 0:
                st.success(f"✅ {parcelas_marcadas} parcela(s) vencida(s) marcada(s) como paga(s) automaticamente")
                parcelas = buscar_parcelas_pendentes(supabase, datetime.combine(data_inicio, datetime.min.time()), datetime.combine(data_fim, datetime.max.time()))
        
        if parcelas:
            # Separar em pagas e pendentes
            parcelas_pendentes = [p for p in parcelas if p['status'] == 'pendente']
            parcelas_pagas = [p for p in parcelas if p['status'] == 'pago']
            
            # Resumo
            total_pendente = sum([float(p['valor_parcela']) for p in parcelas_pendentes])
            total_pago = sum([float(p['valor_parcela']) for p in parcelas_pagas])
            total_geral = total_pendente + total_pago
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                    <div class='metric-card' style='background: linear-gradient(135deg, #E74C3C 0%, #C0392B 100%);'>
                        <h3>⏰ Pendente</h3>
                        <h2>R$ {total_pendente:,.2f}</h2>
                        <p>{len(parcelas_pendentes)} parcela(s)</p>
                    </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                    <div class='metric-card' style='background: linear-gradient(135deg, #28A745 0%, #218838 100%);'>
                        <h3>✅ Pago</h3>
                        <h2>R$ {total_pago:,.2f}</h2>
                        <p>{len(parcelas_pagas)} parcela(s)</p>
                    </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                    <div class='metric-card' style='background: linear-gradient(135deg, #3498DB 0%, #2980B9 100%);'>
                        <h3>📊 Total</h3>
                        <h2>R$ {total_geral:,.2f}</h2>
                        <p>{len(parcelas)} parcela(s)</p>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Tabs para separar pendentes e pagas
            tab1, tab2 = st.tabs([f"⏰ Pendentes ({len(parcelas_pendentes)})", f"✅ Pagas ({len(parcelas_pagas)})"])
            
            with tab1:
                st.markdown("### ⏰ Parcelas Pendentes")
                
                if parcelas_pendentes:
                    for parcela in parcelas_pendentes:
                        data_venc = datetime.fromisoformat(parcela['data_vencimento'].replace('Z', '+00:00'))
                        dias_para_vencer = (data_venc.date() - datetime.now().date()).days
                        
                        # Determinar cor baseado em dias para vencer (atrasadas já são marcadas como pagas automaticamente)
                        if dias_para_vencer <= 7:
                            cor_status = "🟡 Vence em breve"
                            estilo_extra = "border-left: 4px solid #F39C12;"
                        else:
                            cor_status = "🟢 No prazo"
                            estilo_extra = "border-left: 4px solid #28A745;"
                        
                        col1, col2 = st.columns([4, 1])
                        
                        with col1:
                            st.markdown(f"""
                                <div class='box-card' style='{estilo_extra}'>
                                    <strong>{cor_status}</strong><br>
                                    📅 Vencimento: {data_venc.strftime('%d/%m/%Y')}<br>
                                    💵 Valor: R$ {float(parcela['valor_parcela']):,.2f}<br>
                                    📦 Parcela: {parcela['numero_parcela']}/{parcela['total_parcelas']}<br>
                                    {f"📝 {parcela.get('descricao', '')}" if parcela.get('descricao') else ""}
                                </div>
                            """, unsafe_allow_html=True)
                        
                        with col2:
                            st.markdown("<br>", unsafe_allow_html=True)
                            if st.button("✅ Marcar como Paga", key=f"pagar_{parcela['id']}", use_container_width=True):
                                try:
                                    marcar_parcela_paga(supabase, parcela['id'])
                                    st.success("Parcela marcada como paga!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro: {str(e)}")
                else:
                    st.info("✅ Nenhuma parcela pendente no período selecionado")
            
            with tab2:
                st.markdown("### ✅ Parcelas Pagas")
                
                if parcelas_pagas:
                    for parcela in parcelas_pagas:
                        data_venc = datetime.fromisoformat(parcela['data_vencimento'].replace('Z', '+00:00'))
                        data_pag = datetime.fromisoformat(parcela['data_pagamento'].replace('Z', '+00:00')) if parcela.get('data_pagamento') else None
                        
                        col1, col2 = st.columns([4, 1])
                        
                        with col1:
                            st.markdown(f"""
                                <div class='box-card' style='border-left: 4px solid #28A745;'>
                                    <strong>✅ Paga</strong><br>
                                    📅 Vencimento: {data_venc.strftime('%d/%m/%Y')}<br>
                                    💵 Valor: R$ {float(parcela['valor_parcela']):,.2f}<br>
                                    📦 Parcela: {parcela['numero_parcela']}/{parcela['total_parcelas']}<br>
                                    {f"💳 Pago em: {data_pag.strftime('%d/%m/%Y %H:%M')}" if data_pag else ""}<br>
                                    {f"📝 {parcela.get('descricao', '')}" if parcela.get('descricao') else ""}
                                </div>
                            """, unsafe_allow_html=True)
                        
                        with col2:
                            st.markdown("<br>", unsafe_allow_html=True)
                            if st.button("↩️ Desfazer", key=f"desfazer_{parcela['id']}", use_container_width=True):
                                try:
                                    marcar_parcela_pendente(supabase, parcela['id'])
                                    st.success("Status alterado para pendente!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro: {str(e)}")
                else:
                    st.info("Nenhuma parcela paga no período selecionado")
        else:
            st.info("Nenhuma conta a pagar encontrada no período selecionado")
    
    # ==================== CUSTOS PRODUTOS ====================
    elif opcao == "📦 Custos Produtos":
        st.markdown("## 📦 Custos dos Produtos")
        
        # Verificar se a tabela existe tentando fazer uma query
        try:
            teste = supabase.table("singelo_itens_compras").select("id").limit(1).execute()
            
            # Buscar todos os itens
            itens = supabase.table("singelo_itens_compras").select("*").order("created_at", desc=True).limit(200).execute()
            
            if itens.data:
                st.markdown(f"### 📊 Total de {len(itens.data)} itens registrados")
                
                # Criar DataFrame para melhor visualização
                import pandas as pd
                df_itens = []
                for item in itens.data:
                    df_itens.append({
                        "Produto": item['nome_produto'],
                        "Descrição": item.get('descricao', '-')[:50],
                        "Quantidade": float(item['quantidade']),
                        "Valor Unitário": f"R$ {float(item['valor_unitario']):,.2f}",
                        "Valor Total": f"R$ {float(item['valor_total']):,.2f}",
                        "Data": datetime.fromisoformat(item['created_at'].replace('Z', '+00:00')).strftime('%d/%m/%Y')
                    })
                
                df = pd.DataFrame(df_itens)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Resumo por produto
                st.markdown("### 📈 Resumo por Produto")
                produtos_resumo = {}
                for item in itens.data:
                    nome = item['nome_produto']
                    qtd = float(item['quantidade'])
                    valor_unit = float(item['valor_unitario'])
                    valor_total = float(item['valor_total'])
                    
                    if nome not in produtos_resumo:
                        produtos_resumo[nome] = {
                            "quantidade": 0,
                            "valor_total": 0,
                            "compras": 0
                        }
                    
                    produtos_resumo[nome]["quantidade"] += qtd
                    produtos_resumo[nome]["valor_total"] += valor_total
                    produtos_resumo[nome]["compras"] += 1
                
                # Mostrar resumo
                for produto, dados in produtos_resumo.items():
                    valor_medio = dados["valor_total"] / dados["quantidade"] if dados["quantidade"] > 0 else 0
                    st.markdown(f"""
                        **{produto}**
                        - Total comprado: {dados['quantidade']:.2f} unidades
                        - Valor total gasto: R$ {dados['valor_total']:,.2f}
                        - Preço médio: R$ {valor_medio:,.2f}
                        - Número de compras: {dados['compras']}
                    """)
                    st.markdown("---")
            else:
                st.info("Nenhum item de compra registrado ainda. Comece lançando compras com itens!")
                
        except Exception as e:
            st.info("""
            💡 **Informação importante:**
            
            Para ter o controle de custos por produto, você precisa:
            
            1. Criar a tabela **singelo_itens_compras** no Supabase com os campos:
               - id (int8, primary key, auto-increment)
               - compra_id (int8, referência para singelo_compras)
               - nome_produto (text)
               - descricao (text)
               - quantidade (numeric)
               - valor_unitario (numeric)
               - valor_total (numeric)
               - created_at (timestamp with time zone, default now())
            
            2. Execute o SQL abaixo no Supabase:
            
            ```sql
            CREATE TABLE singelo_itens_compras (
                id BIGSERIAL PRIMARY KEY,
                compra_id BIGINT REFERENCES singelo_compras(id) ON DELETE CASCADE,
                nome_produto TEXT NOT NULL,
                descricao TEXT,
                quantidade NUMERIC NOT NULL,
                valor_unitario NUMERIC NOT NULL,
                valor_total NUMERIC NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
            ```
            
            Após criar a tabela, volte aqui para ver os custos dos produtos!
            """)
            st.error(f"⚠️ Erro ao acessar tabela: {str(e)}")
    
    # ==================== FICHA TÉCNICA ====================
    elif opcao == "🧾 Ficha Técnica":
        st.markdown("## 🧾 Ficha Técnica de Produtos")
        
        # Verificar se as tabelas existem
        try:
            teste_materiais = supabase.table("singelo_materiais").select("id").limit(1).execute()
            teste_fichas = supabase.table("singelo_fichas_tecnicas").select("id").limit(1).execute()
            
            # Tabs principais
            tab1, tab2, tab3 = st.tabs(["📦 Materiais/Insumos", "🧾 Fichas Técnicas", "💰 Custo por Produto"])
            
            # ===== TAB 1: MATERIAIS =====
            with tab1:
                st.markdown("### 📦 Cadastro de Materiais")
                
                # Botão para corrigir nomes automaticamente
                col_btn1, col_btn2 = st.columns([3, 1])
                with col_btn2:
                    if st.button("🔧 Corrigir Nomes dos Materiais", use_container_width=True, help="Recupera nomes originais da descrição"):
                        try:
                            # Buscar todos os materiais
                            materiais = supabase.table("singelo_materiais").select("*").execute()
                            
                            if materiais.data:
                                corrigidos = 0
                                import re
                                
                                for mat in materiais.data:
                                    nome_atual = mat.get('nome', '')
                                    descricao = mat.get('descricao', '')
                                    
                                    # Se a descrição existe e é diferente do nome
                                    if descricao and descricao != nome_atual:
                                        # Verificar se a descrição começa com número + "unidades"
                                        match = re.match(r'^(\d+)\s+(unidades?|un)\s+', descricao, re.IGNORECASE)
                                        
                                        # Se a descrição tem quantidade mas o nome não tem
                                        if match and not re.match(r'^(\d+)\s+', nome_atual):
                                            # Usar a descrição como nome
                                            novo_nome = descricao[:100]  # Limitar a 100 caracteres
                                            
                                            supabase.table("singelo_materiais").update({
                                                "nome": novo_nome,
                                                "updated_at": datetime.now().isoformat()
                                            }).eq("id", mat['id']).execute()
                                            
                                            corrigidos += 1
                                
                                if corrigidos > 0:
                                    st.success(f"✅ {corrigidos} material(is) corrigido(s)!")
                                    st.rerun()
                                else:
                                    st.info("ℹ️ Nenhum material precisou de correção")
                        except Exception as e:
                            st.error(f"Erro: {str(e)}")
                
                # Formulário de cadastro
                with st.expander("➕ Adicionar Novo Material", expanded=False):
                    with st.form("form_material"):
                        col1, col2 = st.columns(2)
                        with col1:
                            nome_material = st.text_input("Nome do Material*", placeholder="Ex: Balão Bubble 24 polegadas")
                            unidade = st.selectbox("Unidade de Medida*", 
                                ["unidade", "metro", "centímetro", "litro", "mililitro", "kg", "grama", "pacote", "rolo", "caixa"])
                            custo_unitario = st.number_input("Custo Unitário (R$)*", min_value=0.0, step=0.01, format="%.2f")
                        
                        with col2:
                            descricao_material = st.text_area("Descrição", placeholder="Ex: Balão transparente 24 polegadas")
                            estoque_inicial = st.number_input("Estoque Inicial", min_value=0.0, step=1.0, value=0.0)
                            fornecedor = st.text_input("Fornecedor Principal", placeholder="Nome do fornecedor")
                        
                        observacoes_mat = st.text_area("Observações", placeholder="Informações adicionais...")
                        
                        submitted = st.form_submit_button("💾 Salvar Material", use_container_width=True)
                        
                        if submitted:
                            if nome_material and custo_unitario > 0:
                                try:
                                    material_data = {
                                        "nome": nome_material,
                                        "descricao": descricao_material,
                                        "unidade_medida": unidade,
                                        "estoque_atual": float(estoque_inicial),
                                        "custo_unitario": float(custo_unitario),
                                        "fornecedor_principal": fornecedor,
                                        "observacoes": observacoes_mat,
                                        "ultima_compra_data": datetime.now().date().isoformat()
                                    }
                                    supabase.table("singelo_materiais").insert(material_data).execute()
                                    st.success(f"✅ Material '{nome_material}' cadastrado com sucesso!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao salvar: {str(e)}")
                            else:
                                st.warning("Preencha os campos obrigatórios (*)!")
                
                # Importar itens antigos de NF-es
                st.markdown("---")
                st.markdown("### 📥 Importar Itens de NF-es Antigas")
                
                # Buscar itens que ainda não são materiais
                try:
                    itens_antigos = supabase.table("singelo_itens_compras").select("*").order("created_at", desc=True).execute()
                    
                    if itens_antigos.data:
                        # Filtrar apenas itens que ainda não foram convertidos
                        materiais_existentes = supabase.table("singelo_materiais").select("nome").execute()
                        nomes_materiais = [m['nome'].lower() for m in materiais_existentes.data] if materiais_existentes.data else []
                        
                        itens_nao_convertidos = [
                            item for item in itens_antigos.data 
                            if item['nome_produto'].lower() not in nomes_materiais
                        ]
                        
                        if itens_nao_convertidos:
                            st.info(f"💡 Encontrados **{len(itens_nao_convertidos)} itens** de NF-es antigas que ainda não foram convertidos em materiais!")
                            
                            with st.expander(f"📦 Ver {len(itens_nao_convertidos)} itens para converter"):
                                for idx, item in enumerate(itens_nao_convertidos[:20]):  # Mostrar no máximo 20
                                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                                    
                                    with col1:
                                        nome_original = item['nome_produto']
                                        
                                        # Detectar quantidade no nome
                                        import re
                                        qtd_embalagem = 1
                                        nome_limpo = nome_original
                                        match = re.match(r'(\d+)\s+(unidades?|un|pcs?|peças?)\s+(.+)', nome_original, re.IGNORECASE)
                                        if match:
                                            qtd_embalagem = int(match.group(1))
                                            # Para items antigos mantemos o nome limpo para evitar duplicação
                                            nome_limpo = match.group(3).strip()
                                        
                                        st.write(f"**{nome_limpo}**")
                                        if qtd_embalagem > 1:
                                            st.caption(f"✨ {qtd_embalagem} unidades/embalagem")
                                    
                                    with col2:
                                        qtd = float(item['quantidade'])
                                        valor_unit = float(item['valor_unitario'])
                                        valor_total = float(item['valor_total'])
                                        
                                        # Calcular custo unitário real
                                        qtd_real = qtd * qtd_embalagem
                                        custo_real = valor_total / qtd_real if qtd_real > 0 else valor_unit
                                        
                                        st.metric("Custo/Un", f"R$ {custo_real:.4f}")
                                    
                                    with col3:
                                        st.metric("Qtd", f"{qtd_real:.0f}")
                                    
                                    with col4:
                                        if st.button("➕ Converter", key=f"conv_antigo_{idx}_{item['id']}", use_container_width=True):
                                            try:
                                                # Detectar unidade automaticamente
                                                unidade_auto = detectar_unidade_material(nome_limpo)
                                                
                                                material_data = {
                                                    "nome": nome_limpo,
                                                    "descricao": item.get('descricao', ''),
                                                    "unidade_medida": unidade_auto,
                                                    "estoque_atual": qtd_real,
                                                    "custo_unitario": custo_real,
                                                    "ultima_compra_data": datetime.now().date().isoformat(),
                                                    "fornecedor_principal": "NF-e Importada",
                                                    "observacoes": f"Convertido de item antigo - {qtd_embalagem} unidades/embalagem"
                                                }
                                                supabase.table("singelo_materiais").insert(material_data).execute()
                                                st.success(f"✅ Convertido!")
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Erro: {str(e)}")
                                
                                # Botão para converter todos
                                if st.button("✨ Converter TODOS os itens em materiais", type="primary", use_container_width=True):
                                    sucesso = 0
                                    erros = 0
                                    
                                    for item in itens_nao_convertidos:
                                        try:
                                            nome_original = item['nome_produto']
                                            qtd_embalagem = 1
                                            nome_limpo = nome_original
                                            
                                            import re
                                            match = re.match(r'(\d+)\s+(unidades?|un|pcs?|peças?)\s+(.+)', nome_original, re.IGNORECASE)
                                            if match:
                                                qtd_embalagem = int(match.group(1))
                                                nome_limpo = match.group(3).strip()
                                            
                                            qtd = float(item['quantidade'])
                                            valor_total = float(item['valor_total'])
                                            qtd_real = qtd * qtd_embalagem
                                            custo_real = valor_total / qtd_real if qtd_real > 0 else float(item['valor_unitario'])
                                            
                                            material_data = {
                                                "nome": nome_limpo,
                                                "descricao": item.get('descricao', ''),
                                                "unidade_medida": "unidade",
                                                "estoque_atual": qtd_real,
                                                "custo_unitario": custo_real,
                                                "ultima_compra_data": datetime.now().date().isoformat(),
                                                "fornecedor_principal": "NF-e Importada",
                                                "observacoes": f"Convertido automaticamente - {qtd_embalagem} unidades/embalagem"
                                            }
                                            supabase.table("singelo_materiais").insert(material_data).execute()
                                            sucesso += 1
                                        except:
                                            erros += 1
                                    
                                    st.success(f"✅ Conversão concluída! {sucesso} materiais criados, {erros} erros.")
                                    st.rerun()
                        else:
                            st.success("✅ Todos os itens de NF-es antigas já foram convertidos em materiais!")
                    else:
                        st.info("Nenhum item antigo encontrado.")
                except Exception as e:
                    st.warning(f"Não foi possível verificar itens antigos: {str(e)}")
                
                # Listar materiais cadastrados
                st.markdown("---")
                st.markdown("### 📋 Materiais Cadastrados")
                
                materiais = supabase.table("singelo_materiais").select("*").order("nome").execute()
                
                if materiais.data:
                    import pandas as pd
                    
                    st.markdown("#### 🔧 Editar Materiais")
                    st.info("💡 Clique em um material para editar unidade de medida, custo ou estoque")
                    
                    for mat in materiais.data:
                        with st.expander(f"📦 {mat['nome']} ({mat['unidade_medida']}) - R$ {float(mat['custo_unitario']):.2f}"):
                            with st.form(key=f"form_edit_{mat['id']}"):
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    nome_edit = st.text_input("Nome", value=mat['nome'], key=f"nome_{mat['id']}")
                                    
                                    # Detectar unidade sugerida
                                    unidade_sugerida = detectar_unidade_material(mat['nome'])
                                    unidades_opcoes = ["unidade", "metro", "centímetro", "litro", "mililitro", "kg", "grama", "pacote", "rolo"]
                                    indice_atual = unidades_opcoes.index(mat['unidade_medida']) if mat['unidade_medida'] in unidades_opcoes else 0
                                    
                                    unidade_edit = st.selectbox(
                                        "Unidade de Medida", 
                                        unidades_opcoes,
                                        index=indice_atual,
                                        key=f"unid_{mat['id']}",
                                        help=f"✨ Sugerido: {unidade_sugerida}"
                                    )
                                
                                with col2:
                                    custo_edit = st.number_input(
                                        "Custo Unitário (R$)", 
                                        value=float(mat['custo_unitario']),
                                        min_value=0.0,
                                        step=0.01,
                                        format="%.4f",
                                        key=f"custo_{mat['id']}"
                                    )
                                    estoque_edit = st.number_input(
                                        "Estoque Atual", 
                                        value=float(mat['estoque_atual']),
                                        min_value=0.0,
                                        step=1.0,
                                        key=f"estoque_{mat['id']}"
                                    )
                                
                                with col3:
                                    fornecedor_edit = st.text_input(
                                        "Fornecedor", 
                                        value=mat.get('fornecedor_principal', ''),
                                        key=f"forn_{mat['id']}"
                                    )
                                    descricao_edit = st.text_area(
                                        "Descrição", 
                                        value=mat.get('descricao', ''),
                                        key=f"desc_{mat['id']}"
                                    )
                                
                                col_btn1, col_btn2 = st.columns(2)
                                with col_btn1:
                                    if st.form_submit_button("💾 Salvar Alterações", use_container_width=True):
                                        try:
                                            supabase.table("singelo_materiais").update({
                                                "nome": nome_edit,
                                                "unidade_medida": unidade_edit,
                                                "custo_unitario": custo_edit,
                                                "estoque_atual": estoque_edit,
                                                "fornecedor_principal": fornecedor_edit,
                                                "descricao": descricao_edit,
                                                "updated_at": datetime.now().isoformat()
                                            }).eq("id", mat['id']).execute()
                                            st.success("✅ Material atualizado!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Erro: {str(e)}")
                                
                                with col_btn2:
                                    if st.form_submit_button("🗑️ Excluir", use_container_width=True):
                                        try:
                                            supabase.table("singelo_materiais").delete().eq("id", mat['id']).execute()
                                            st.success("✅ Material excluído!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Erro: {str(e)}")
                    
                    # Tabela resumo
                    st.markdown("---")
                    st.markdown("#### 📊 Resumo de Materiais")
                    
                    df_materiais = []
                    for mat in materiais.data:
                        df_materiais.append({
                            "Material": mat['nome'],
                            "Unidade": mat['unidade_medida'],
                            "Custo/Un": f"R$ {float(mat['custo_unitario']):.4f}",
                            "Estoque": f"{float(mat['estoque_atual']):.2f}",
                            "Valor Estoque": f"R$ {float(mat['estoque_atual']) * float(mat['custo_unitario']):.2f}",
                            "Fornecedor": mat.get('fornecedor_principal', '-')
                        })
                    
                    df = pd.DataFrame(df_materiais)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # Totalizador
                    valor_total_estoque = sum([float(m['estoque_atual']) * float(m['custo_unitario']) for m in materiais.data])
                    st.info(f"💰 **Valor Total em Estoque:** R$ {valor_total_estoque:,.2f}")
                else:
                    st.info("Nenhum material cadastrado ainda.")
            
            # ===== TAB 2: FICHAS TÉCNICAS =====
            with tab2:
                st.markdown("### 🧾 Composição dos Produtos")
                
                # Usar a mesma lista de produtos disponível em Lançar Venda
                PRODUTOS = BOXES
                
                # Seletor de produto
                col1, col2 = st.columns([2, 1])
                with col1:
                    produto_selecionado = st.selectbox("Selecione o Produto", PRODUTOS)
                with col2:
                    if st.button("🔄 Atualizar", use_container_width=True):
                        st.rerun()
                
                st.markdown(f"### Ficha Técnica: **{produto_selecionado}**")
                
                # Formulário para adicionar material à ficha
                with st.expander("➕ Adicionar Material à Ficha", expanded=False):
                    # Buscar materiais disponíveis
                    materiais_disp = supabase.table("singelo_materiais").select("*").order("nome").execute()
                    
                    if materiais_disp.data:
                        # Criar dicionário de materiais com informações completas
                        materiais_dict = {f"{m['nome']} ({m['unidade_medida']})": m for m in materiais_disp.data}
                        
                        material_nome = st.selectbox("Material", list(materiais_dict.keys()), key="sel_material_ficha")
                        material_selecionado = materiais_dict[material_nome]
                        unidade = material_selecionado['unidade_medida']
                        
                        # Verificar se o nome do material indica quantidade na embalagem (ex: "50 Ponteira...")
                        import re
                        nome_material = material_selecionado['nome']
                        qtd_embalagem = 1
                        match = re.match(r'^(\d+)\s+(.+)', nome_material)
                        if match:
                            qtd_embalagem = int(match.group(1))
                            nome_sem_qtd = match.group(2).strip()
                            
                            # Mostrar alerta explicativo
                            st.warning(f"""
                            ⚠️ **Atenção!** Este material está cadastrado como **"{nome_material}"**
                            
                            Parece que vêm **{qtd_embalagem} unidades** na embalagem. 
                            
                            💡 **Custo no banco:** R$ {float(material_selecionado['custo_unitario']):,.4f} (custo da embalagem com {qtd_embalagem} un)  
                            💡 **Custo por unidade individual:** R$ {float(material_selecionado['custo_unitario'])/qtd_embalagem:,.4f}
                            
                            Se você quer usar **unidades individuais**, coloque a quantidade de unidades que precisa.
                            O sistema calculará o custo correto automaticamente.
                            """)
                        
                        # Inicializar quantidade
                        quantidade_usar = 0.0
                        
                        # Verificar se é material que usa área (metro, centímetro, rolo)
                        usa_area = unidade in ['metro', 'centímetro', 'rolo']
                        
                        if usa_area:
                            st.info(f"💡 Para materiais em **{unidade}**, você pode informar dimensões (comprimento × largura) para cálculo automático de área")
                            
                            tipo_calculo = st.radio(
                                "Tipo de cálculo",
                                ["Quantidade simples", "Área (comprimento × largura)"],
                                help="Escolha como quer calcular a quantidade",
                                key="tipo_calc_ficha"
                            )
                            
                            if tipo_calculo == "Área (comprimento × largura)":
                                st.markdown("#### 📐 Informe as dimensões:")
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    comprimento = st.number_input(
                                        f"Comprimento ({unidade})", 
                                        min_value=0.0, 
                                        step=0.01, 
                                        format="%.4f",
                                        help=f"Ex: 0,15 para 15cm (se unidade é metro)",
                                        key="comp_ficha"
                                    )
                                with col_b:
                                    largura = st.number_input(
                                        f"Largura ({unidade})", 
                                        min_value=0.0, 
                                        step=0.01, 
                                        format="%.4f",
                                        help=f"Ex: 0,04 para 4cm (se unidade é metro)",
                                        key="larg_ficha"
                                    )
                                
                                # Calcular área automaticamente
                                area = comprimento * largura
                                quantidade_usar = area
                                
                                if area > 0:
                                    st.success(f"📐 Área calculada: **{area:.6f} {unidade}²**")
                                    custo_material = float(material_selecionado['custo_unitario'])
                                    # Ajustar custo se material tem quantidade na embalagem
                                    if qtd_embalagem > 1:
                                        custo_material = custo_material / qtd_embalagem
                                    custo_total = area * custo_material
                                    st.metric("💰 Custo estimado", f"R$ {custo_total:.4f}")
                                else:
                                    st.warning("Informe o comprimento e largura para calcular a área")
                            else:
                                quantidade_usar = st.number_input(
                                    f"Quantidade Necessária ({unidade})", 
                                    min_value=0.0, 
                                    step=0.01, 
                                    format="%.4f",
                                    help="Digite a quantidade que será usada",
                                    key="qtd_simples_ficha"
                                )
                                if quantidade_usar > 0:
                                    custo_material = float(material_selecionado['custo_unitario'])
                                    # Ajustar custo se material tem quantidade na embalagem
                                    if qtd_embalagem > 1:
                                        custo_material = custo_material / qtd_embalagem
                                    custo_total = quantidade_usar * custo_material
                                    st.metric("💰 Custo estimado", f"R$ {custo_total:.4f}")
                        else:
                            quantidade_usar = st.number_input(
                                f"Quantidade Necessária ({unidade})", 
                                min_value=0.0, 
                                step=0.01, 
                                format="%.4f",
                                help="Digite a quantidade que será usada",
                                key="qtd_ficha"
                            )
                            if quantidade_usar > 0:
                                custo_material = float(material_selecionado['custo_unitario'])
                                # Ajustar custo se material tem quantidade na embalagem
                                if qtd_embalagem > 1:
                                    custo_material = custo_material / qtd_embalagem
                                custo_total = quantidade_usar * custo_material
                                st.metric("💰 Custo estimado", f"R$ {custo_total:.4f}")
                        
                        obs_ficha = st.text_input("Observações", placeholder="Ex: usar 15cm de comprimento × 4cm de altura", key="obs_ficha")
                        
                        if st.button("➕ Adicionar à Ficha", use_container_width=True, type="primary", key="btn_add_ficha"):
                            if quantidade_usar > 0:
                                try:
                                    material_id = material_selecionado['id']
                                    ficha_data = {
                                        "produto": produto_selecionado,
                                        "material_id": material_id,
                                        "quantidade": float(quantidade_usar),
                                        "observacoes": obs_ficha
                                    }
                                    supabase.table("singelo_fichas_tecnicas").insert(ficha_data).execute()
                                    st.success(f"✅ Material adicionado à ficha!")
                                    st.rerun()
                                except Exception as e:
                                    if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                                        st.error("Este material já está na ficha deste produto!")
                                    else:
                                        st.error(f"Erro: {str(e)}")
                            else:
                                st.warning("⚠️ Informe a quantidade antes de adicionar!")
                    else:
                        st.warning("Cadastre materiais primeiro na aba 'Materiais/Insumos'!")
                
                # Mostrar ficha técnica do produto
                st.markdown("---")
                st.markdown("### 📋 Materiais Necessários")
                
                # Buscar ficha técnica com join de materiais
                fichas = supabase.table("singelo_fichas_tecnicas").select("*, singelo_materiais(*)").eq("produto", produto_selecionado).execute()
                
                if fichas.data:
                    custo_total_produto = 0
                    
                    for item in fichas.data:
                        material = item['singelo_materiais']
                        quantidade = float(item['quantidade'])
                        custo_unit = float(material['custo_unitario'])
                        
                        # Verificar se o material tem quantidade na embalagem (ex: "50 Ponteira...")
                        import re
                        nome_material = material['nome']
                        qtd_embalagem = 1
                        match = re.match(r'^(\d+)\s+(.+)', nome_material)
                        if match:
                            qtd_embalagem = int(match.group(1))
                            # Ajustar custo unitário para unidade individual
                            custo_unit = custo_unit / qtd_embalagem
                        
                        custo_item = quantidade * custo_unit
                        custo_total_produto += custo_item
                        
                        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
                        
                        with col1:
                            st.write(f"**{material['nome']}**")
                            if item.get('observacoes'):
                                st.caption(item['observacoes'])
                        with col2:
                            st.write(f"{quantidade:.4f}")
                        with col3:
                            st.write(material['unidade_medida'])
                        with col4:
                            st.write(f"R$ {custo_item:.2f}")
                        with col5:
                            if st.button("🗑️", key=f"del_{item['id']}"):
                                supabase.table("singelo_fichas_tecnicas").delete().eq("id", item['id']).execute()
                                st.rerun()
                    
                    st.markdown("---")
                    st.success(f"### 💰 Custo Total de Produção: R$ {custo_total_produto:.2f}")
                else:
                    st.info("Nenhum material adicionado nesta ficha ainda.")
            
            # ===== TAB 3: CUSTO POR PRODUTO =====
            with tab3:
                st.markdown("### 💰 Resumo de Custos por Produto")
                
                # Buscar todas as fichas e calcular custos
                todas_fichas = supabase.table("singelo_fichas_tecnicas").select("*, singelo_materiais(*)").execute()
                
                if todas_fichas.data:
                    custos_por_produto = {}
                    
                    for item in todas_fichas.data:
                        produto = item['produto']
                        material = item['singelo_materiais']
                        quantidade = float(item['quantidade'])
                        custo_unit = float(material['custo_unitario'])
                        
                        # Verificar se o material tem quantidade na embalagem (ex: "50 Ponteira...")
                        import re
                        nome_material = material['nome']
                        qtd_embalagem = 1
                        match = re.match(r'^(\d+)\s+(.+)', nome_material)
                        if match:
                            qtd_embalagem = int(match.group(1))
                            # Ajustar custo unitário para unidade individual
                            custo_unit = custo_unit / qtd_embalagem
                        
                        custo_item = quantidade * custo_unit
                        
                        if produto not in custos_por_produto:
                            custos_por_produto[produto] = {
                                'custo_total': 0,
                                'materiais': []
                            }
                        
                        custos_por_produto[produto]['custo_total'] += custo_item
                        custos_por_produto[produto]['materiais'].append({
                            'nome': material['nome'],
                            'quantidade': quantidade,
                            'unidade': material['unidade_medida'],
                            'custo': custo_item
                        })
                    
                    # Mostrar resumo
                    for produto, dados in custos_por_produto.items():
                        with st.expander(f"**{produto}** - Custo: R$ {dados['custo_total']:.2f}"):
                            for mat in dados['materiais']:
                                st.write(f"- {mat['nome']}: {mat['quantidade']:.4f} {mat['unidade']} = R$ {mat['custo']:.2f}")
                            st.markdown(f"**Total:** R$ {dados['custo_total']:.2f}")
                    
                    # Gráfico de custos (opcional)
                    st.markdown("---")
                    import pandas as pd
                    df_custos = pd.DataFrame([
                        {"Produto": produto, "Custo de Produção": dados['custo_total']}
                        for produto, dados in custos_por_produto.items()
                    ]).sort_values("Custo de Produção", ascending=False)
                    
                    st.bar_chart(df_custos.set_index("Produto"))
                else:
                    st.info("Nenhuma ficha técnica cadastrada ainda.")
        
        except Exception as e:
            st.info("""
            💡 **Configure o sistema de Ficha Técnica:**
            
            Para usar o controle de custos de produção, execute este SQL no Supabase:
            
            📄 Arquivo: `criar_tabelas_ficha_tecnica.sql`
            
            Este arquivo já está criado na pasta do projeto!
            """)
            
            with st.expander("📋 Ver SQL Completo"):
                st.code("""
-- SISTEMA DE FICHA TÉCNICA DE PRODUTOS
-- Execute este SQL no Supabase SQL Editor

-- Tabela de Materiais/Insumos
CREATE TABLE singelo_materiais (
    id BIGSERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    descricao TEXT,
    unidade_medida TEXT NOT NULL,
    estoque_atual NUMERIC DEFAULT 0,
    custo_unitario NUMERIC NOT NULL,
    ultima_compra_data DATE,
    fornecedor_principal TEXT,
    observacoes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabela de Fichas Técnicas
CREATE TABLE singelo_fichas_tecnicas (
    id BIGSERIAL PRIMARY KEY,
    produto TEXT NOT NULL,
    material_id BIGINT REFERENCES singelo_materiais(id) ON DELETE CASCADE,
    quantidade NUMERIC NOT NULL,
    observacoes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(produto, material_id)
);

-- Habilitar Row Level Security
ALTER TABLE singelo_materiais ENABLE ROW LEVEL SECURITY;
ALTER TABLE singelo_fichas_tecnicas ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Permitir todas operações em materiais" ON singelo_materiais
FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Permitir todas operações em fichas_tecnicas" ON singelo_fichas_tecnicas
FOR ALL USING (true) WITH CHECK (true);
                """, language="sql")
            
            st.warning(f"Detalhes do erro: {str(e)}")
    
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
                
                # Mostrar cada compra com botão de editar e excluir
                for compra in compras:
                    col1, col2, col3, col4, col5 = st.columns([2, 2, 3, 1, 1])
                    
                    data_formatada = datetime.fromisoformat(compra['data'].replace('Z', '+00:00')).strftime('%d/%m/%Y %H:%M')
                    descricao = compra.get('descricao', '-')
                    
                    # Se a descrição tiver múltiplas linhas (itens), mostrar só a primeira linha
                    descricao_curta = descricao.split('\n')[0] if descricao else '-'
                    
                    with col1:
                        st.write(f"📅 {data_formatada}")
                    with col2:
                        st.write(f"💵 R$ {float(compra['valor_total']):,.2f}")
                    with col3:
                        # Usar expander para descrições longas
                        if '\n' in descricao:
                            with st.expander(f"📝 {descricao_curta}"):
                                st.text(descricao)
                        else:
                            st.write(f"📝 {descricao_curta}")
                    with col4:
                        if st.button("✏️", key=f"edit_compra_{compra['id']}", help="Editar", use_container_width=True):
                            st.session_state.editando_compra = compra
                    with col5:
                        if st.button("🗑️", key=f"del_compra_{compra['id']}", help="Excluir", use_container_width=True):
                            try:
                                excluir_compra(supabase, compra['id'])
                                st.success("✅ Compra excluída!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Erro: {str(e)}")
                    
                    st.markdown("---")
                
                # Modal de edição de compra
                if 'editando_compra' in st.session_state and st.session_state.editando_compra:
                    compra = st.session_state.editando_compra
                    data_compra_obj = datetime.fromisoformat(compra['data'].replace('Z', '+00:00'))
                    
                    # Buscar parcelas atuais
                    parcelas_atuais = supabase.table("singelo_parcelas_compras").select("*").eq("compra_id", compra['id']).execute()
                    num_parcelas_atual = len(parcelas_atuais.data) if parcelas_atuais.data else 1
                    
                    with st.form(f"form_edit_compra_{compra['id']}"):
                        st.markdown(f"### ✏️ Editar Compra")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            novo_valor = st.number_input(
                                "💵 Valor Total (R$)",
                                min_value=0.01,
                                value=float(compra['valor_total']),
                                step=0.01,
                                format="%.2f"
                            )
                        
                        with col2:
                            novo_num_parcelas = st.selectbox(
                                "💳 Número de Parcelas",
                                options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                                index=num_parcelas_atual - 1 if num_parcelas_atual <= 12 else 0,
                                format_func=lambda x: f"{x}x" if x > 1 else "À vista"
                            )
                        
                        nova_descricao = st.text_area(
                            "📝 Descrição",
                            value=compra.get('descricao', ''),
                            height=100
                        )
                        
                        # Aviso se mudar número de parcelas
                        if novo_num_parcelas != num_parcelas_atual:
                            st.warning(f"⚠️ **ATENÇÃO:** Você está alterando o número de parcelas de {num_parcelas_atual}x para {novo_num_parcelas}x. Todas as parcelas já lançadas serão recalculadas!")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("💾 Salvar", use_container_width=True, type="primary"):
                                try:
                                    # Atualizar compra
                                    atualizar_compra(supabase, compra['id'], novo_valor, nova_descricao)
                                    
                                    # Se mudou o número de parcelas, recalcular
                                    if novo_num_parcelas != num_parcelas_atual:
                                        recalcular_parcelas(supabase, compra['id'], novo_valor, novo_num_parcelas, data_compra_obj)
                                        st.success(f"✅ Compra atualizada e {novo_num_parcelas} parcelas recalculadas!")
                                    else:
                                        st.success("✅ Compra atualizada!")
                                    
                                    del st.session_state.editando_compra
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Erro: {str(e)}")
                        with col2:
                            if st.form_submit_button("❌ Cancelar", use_container_width=True):
                                del st.session_state.editando_compra
                                st.rerun()
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
                
                # Mostrar cada venda com botão de editar e excluir
                for venda in vendas:
                    col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 2, 1.5, 1, 1.5, 0.7, 0.7])
                    
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
                        if st.button("✏️", key=f"edit_venda_{venda['id']}", help="Editar", use_container_width=True):
                            st.session_state.editando_venda = venda
                    with col7:
                        if st.button("🗑️", key=f"del_venda_{venda['id']}", help="Excluir", use_container_width=True):
                            try:
                                excluir_venda(supabase, venda['id'])
                                st.success("✅ Venda excluída!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Erro: {str(e)}")
                    
                    st.markdown("---")
                
                # Modal de edição de venda
                if 'editando_venda' in st.session_state and st.session_state.editando_venda:
                    venda = st.session_state.editando_venda
                    
                    with st.form(f"form_edit_venda_{venda['id']}"):
                        st.markdown(f"### ✏️ Editar Venda")
                        
                        st.markdown("#### 📦 Informações do Produto")
                        col1, col2 = st.columns(2)
                        with col1:
                            novo_produto = st.selectbox("🎁 Box", options=BOXES, index=BOXES.index(venda['produto']) if venda['produto'] in BOXES else 0)
                        with col2:
                            novo_tamanho = st.selectbox("📏 Tamanho", options=list(TAMANHOS.keys()), 
                                                       index=list(TAMANHOS.keys()).index(venda.get('tamanho', 'Box mini')) if venda.get('tamanho') in TAMANHOS.keys() else 0)
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            nova_quantidade = st.number_input("📦 Quantidade", min_value=1, value=venda['quantidade'], step=1)
                        with col2:
                            novo_valor = st.number_input("💵 Valor (R$)", min_value=0.01, value=float(venda['valor_total']), step=0.01, format="%.2f")
                        with col3:
                            nova_taxa = st.number_input("🚚 Taxa Entrega (R$)", min_value=0.00, value=float(venda.get('taxa_entrega', 0)), step=0.01, format="%.2f")
                        
                        st.markdown("---")
                        st.markdown("#### 📍 Endereço de Entrega")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            # Converter string ISO para date se necessário
                            data_entrega_atual = None
                            if venda.get('data_entrega'):
                                try:
                                    if isinstance(venda['data_entrega'], str):
                                        data_entrega_atual = datetime.fromisoformat(venda['data_entrega'].replace('Z', '+00:00')).date()
                                    else:
                                        data_entrega_atual = venda['data_entrega']
                                except:
                                    data_entrega_atual = datetime.now().date()
                            else:
                                data_entrega_atual = datetime.now().date()
                            
                            nova_data_entrega = st.date_input(
                                "📅 Data de Entrega",
                                value=data_entrega_atual,
                                format="DD/MM/YYYY"
                            )
                        with col2:
                            novo_cep = st.text_input("📮 CEP", value=venda.get('cep', ''), max_chars=9)
                        
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            novo_logradouro = st.text_input("🏠 Rua/Avenida", value=venda.get('logradouro', ''))
                        with col2:
                            novo_numero = st.text_input("🔢 Número", value=venda.get('numero', ''))
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            novo_bairro = st.text_input("🏘️ Bairro", value=venda.get('bairro', ''))
                        with col2:
                            novo_complemento = st.text_input("🏢 Complemento", value=venda.get('complemento', ''))
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            nova_cidade = st.text_input("🌆 Cidade", value=venda.get('cidade', ''))
                        with col2:
                            novo_uf = st.text_input("🗺️ Estado (UF)", value=venda.get('uf', ''), max_chars=2)
                        
                        st.markdown("---")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("💾 Salvar", use_container_width=True, type="primary"):
                                try:
                                    atualizar_venda(supabase, venda['id'], novo_produto, nova_quantidade, novo_valor, nova_taxa, novo_tamanho,
                                                   data_entrega=nova_data_entrega, cep=novo_cep, 
                                                   logradouro=novo_logradouro, numero=novo_numero,
                                                   complemento=novo_complemento, bairro=novo_bairro,
                                                   cidade=nova_cidade, uf=novo_uf)
                                    st.success("✅ Venda atualizada!")
                                    del st.session_state.editando_venda
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Erro: {str(e)}")
                        with col2:
                            if st.form_submit_button("❌ Cancelar", use_container_width=True):
                                del st.session_state.editando_venda
                                st.rerun()
                
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
                
                # Mostrar cada entrega com botão de editar e excluir
                for entrega in entregas:
                    col1, col2, col3, col4, col5 = st.columns([2, 2, 3, 1, 1])
                    
                    data_formatada = datetime.fromisoformat(entrega['data'].replace('Z', '+00:00')).strftime('%d/%m/%Y %H:%M')
                    
                    with col1:
                        st.write(f"📅 {data_formatada}")
                    with col2:
                        st.write(f"💵 R$ {float(entrega['custo_entregador']):,.2f}")
                    with col3:
                        st.write(f"📝 {entrega.get('descricao', '-')}")
                    with col4:
                        if st.button("✏️", key=f"edit_entrega_{entrega['id']}", help="Editar", use_container_width=True):
                            st.session_state.editando_entrega = entrega
                    with col5:
                        if st.button("🗑️", key=f"del_entrega_{entrega['id']}", help="Excluir", use_container_width=True):
                            try:
                                excluir_entrega(supabase, entrega['id'])
                                st.success("✅ Custo excluído!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Erro: {str(e)}")
                    
                    st.markdown("---")
                
                # Modal de edição de entrega
                if 'editando_entrega' in st.session_state and st.session_state.editando_entrega:
                    entrega = st.session_state.editando_entrega
                    
                    with st.form(f"form_edit_entrega_{entrega['id']}"):
                        st.markdown(f"### ✏️ Editar Custo de Entrega")
                        
                        novo_custo = st.number_input(
                            "💵 Custo (R$)",
                            min_value=0.01,
                            value=float(entrega['custo_entregador']),
                            step=0.01,
                            format="%.2f"
                        )
                        
                        nova_descricao = st.text_area(
                            "📝 Descrição",
                            value=entrega.get('descricao', ''),
                            height=100
                        )
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("💾 Salvar", use_container_width=True, type="primary"):
                                try:
                                    atualizar_entrega(supabase, entrega['id'], novo_custo, nova_descricao)
                                    st.success("✅ Custo atualizado!")
                                    del st.session_state.editando_entrega
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Erro: {str(e)}")
                        with col2:
                            if st.form_submit_button("❌ Cancelar", use_container_width=True):
                                del st.session_state.editando_entrega
                                st.rerun()
                    
                    st.markdown("---")
            else:
                st.info("📭 Nenhum custo de entrega registrado ainda")

if __name__ == "__main__":
    main()
