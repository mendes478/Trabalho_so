import socket
import threading
import time
from dataclasses import dataclass
from cliente1 import Jokenpo

class EstadoMemoriaCompartilhada():
    # 1. ANOTAÇÕES DE TIPO (O molde/documentação para o editor de código)
    jogadas_jogador1: str
    jogador_jogador2: str
    fase_jogador1: int
    fase_jogador2: int
    j1_pronto: bool
    j2_pronto: bool
    j1_reordenado: bool          # Adicionado para a Fase 2
    j2_reordenado: bool          # Adicionado para a Fase 2
    resultado_final: str         # Adicionado para a Fase 3
    processamento_concluido: bool # Adicionado para a Fase 3
    vitorias_jogador1: int
    vitorias_jogador2: int
    j1_fim_rodada: bool
    j2_fim_rodada: bool
    lock_memoria: threading.Lock

    # 2. O CONSTRUTOR (Onde a memória é alocada de verdade quando você instancia)
    def __init__(self):
        self.jogadas_jogador1 = ""
        self.jogador_jogador2 = ""
        self.fase_jogador1 = 1
        self.fase_jogador2 = 1
        self.j1_pronto = False
        self.j2_pronto = False
        self.j1_reordenado = False
        self.j2_reordenado = False
        self.resultado_final = ""
        self.processamento_concluido = False
        self.vitorias_jogador1 = 0
        self.vitorias_jogador2 = 0
        self.j1_fim_rodada = False
        self.j2_fim_rodada = False
        self.lock_memoria = threading.Lock()

def gerenciar_cliente(conexao, id_jogador, estado_jogo: EstadoMemoriaCompartilhada):
    print(f"[THREAD] Iniciada para o Jogador {id_jogador}")
    try:
        while True:
            dados = conexao.recv(1024).decode('utf-8')
            
            if not dados or dados.lower() == 'sair':
                print(f"[SERVIDOR] Jogador {id_jogador} solicitou desconexão ou saiu.")
                break
                
            print(f"[JOGADOR {id_jogador}]: {dados}")
            
            # 1. Atualiza os dados na memória de forma protegida
            with estado_jogo.lock_memoria:
                if id_jogador == 1:
                    estado_jogo.jogadas_jogador1 = dados
                    estado_jogo.j1_fim_rodada = False
                else:
                    estado_jogo.jogador_jogador2 = dados
                    estado_jogo.j2_fim_rodada = False
                
                atualiza_fase(estado_jogo, id_jogador)
                deixa_pronto(estado_jogo, id_jogador)

            # 2. BARREIRA DE ESPERA: Ambas as threads param aqui e esperam as duas ficarem prontas
            while True:
                with estado_jogo.lock_memoria:
                    if estado_jogo.j1_pronto and estado_jogo.j2_pronto:
                        break
                time.sleep(0.1)

            coordena_reordenacao(conexao, id_jogador, estado_jogo)    

            # 3. PROCESSAMENTO EXCLUSIVO DA THREAD 1
            # While true atrapalhava o cliente 2 deixa ele preso e nao reiniciava
            if id_jogador == 1:
                with estado_jogo.lock_memoria:
                    resultado = computar_vencedor(estado_jogo.jogadas_jogador1, estado_jogo.jogador_jogador2, estado_jogo)
                    estado_jogo.resultado_final = resultado
                    estado_jogo.processamento_concluido = True

            # 4. SEGUNDA BARREIRA DE ESPERA (Para o Jogador 2 esperar o cálculo do Jogador 1)
            while True:
                with estado_jogo.lock_memoria:
                    if getattr(estado_jogo, 'processamento_concluido', False):
                        break
                time.sleep(0.1)

            # 5. ENVIO DOS RESULTADOS SINCRONIZADOS
            with estado_jogo.lock_memoria:
                resposta = estado_jogo.resultado_final
            
            conexao.send(resposta.encode('utf-8'))

            with estado_jogo.lock_memoria:
                if id_jogador == 1:
                    estado_jogo.j1_fim_rodada = True
                else:
                    estado_jogo.j2_fim_rodada = True     

            while True:
                with estado_jogo.lock_memoria:
                    if getattr(estado_jogo, 'j1_fim_rodada', False) and getattr(estado_jogo, 'j2_fim_rodada', False):
                        break
                time.sleep(0.1)
                
            # 6. LIMPEZA DE FLAGS PARA A PRÓXIMA RODADA
            with estado_jogo.lock_memoria:
                if id_jogador == 1:
                    estado_jogo.j1_pronto = False
                    estado_jogo.j1_reordenado = False 
                    estado_jogo.processamento_concluido = False 
                else:
                    estado_jogo.j2_pronto = False
                    estado_jogo.j2_reordenado = False 
                    

    except Exception as e:
        print(f"[ERRO] Exceção na thread do Jogador {id_jogador}: {e}")
    finally:
        conexao.close()

def atualiza_fase(estado: EstadoMemoriaCompartilhada, id_jogador):
    if id_jogador == 1:
        estado.fase_jogador1 += 1
    elif id_jogador == 2:
        estado.fase_jogador2 += 1    

def deixa_pronto(estado: EstadoMemoriaCompartilhada, id_jogador):
    if id_jogador == 1:
        estado.j1_pronto = True
    elif id_jogador == 2:
        estado.j2_pronto = True


def computar_vencedor(jogadas_j1, jogadas_j2, estado_jogo: EstadoMemoriaCompartilhada) -> str:
    regras_vitoria = {
        'R': 'T',
        'T': 'P',
        'P': 'R'
    }
    
    pontos_j1 = 0
    pontos_j2 = 0
    
    for i in range(5):
        j1 = jogadas_j1[i].upper()
        j2 = jogadas_j2[i].upper()
        
        if j1 == j2:
            print(f"Rodada {i+1}: {j1} vs {j2} -> Empate")
            continue
            
        if regras_vitoria[j1] == j2:
            pontos_j1 += 1
            print(f"Rodada {i+1}: {j1} vs {j2} -> Ponto para Jogador 1")
        else:
            pontos_j2 += 1
            print(f"Rodada {i+1}: {j1} vs {j2} -> Ponto para Jogador 2")
            
    print("-" * 30)
    if pontos_j1 > pontos_j2:
        estado_jogo.vitorias_jogador1 += 1
        resultado_partida = f"Jogador 1 Venceu o jogo! ({pontos_j1}x{pontos_j2})"
    elif pontos_j2 > pontos_j1:
        estado_jogo.vitorias_jogador2 += 1
        resultado_partida = f"Jogador 2 Venceu o jogo! ({pontos_j2}x{pontos_j1})"
    else:
        resultado_partida = f"O jogo terminou em Empate! ({pontos_j1}x{pontos_j2})"
        
    return f"{resultado_partida} | PLACAR GERAL: {estado_jogo.vitorias_jogador1} x {estado_jogo.vitorias_jogador2}"
    
import time

def coordena_reordenacao(conexao, id_jogador, estado_jogo: EstadoMemoriaCompartilhada):
    """
    Coordena a Fase 2 (Revelação e Reordenação).
    Cada jogador recebe o deck original do oponente, faz sua reordenação e 
    atualiza a memória compartilhada com a nova estratégia.
    """
    print(f"[FASE 2] Iniciada reordenação para Jogador {id_jogador}")
    
    # 1. LEITURA CRUZADA: Pegar o deck do oponente de forma segura
    with estado_jogo.lock_memoria:
        if id_jogador == 1:
            deck_adversario = estado_jogo.jogador_jogador2
        else:
            deck_adversario = estado_jogo.jogadas_jogador1

    # 2. COMUNICAÇÃO: Envia o deck do adversário para o cliente
    # O cliente vai exibir isso na tela e pedir a nova ordem do usuário
    mensagem_envio = deck_adversario
    conexao.send(mensagem_envio.encode('utf-8'))
    
    # 3. REDE: Recebe a nova string com o deck reordenado do cliente
    novo_deck = conexao.recv(1024).decode('utf-8')
    print(f"[JOGADOR {id_jogador} REORDENOU]: {novo_deck}")
    
    # 4. ESCRITA: Atualiza a memória compartilhada com as jogadas finais
    with estado_jogo.lock_memoria:
        if id_jogador == 1:
            estado_jogo.jogadas_jogador1 = novo_deck
            # Usando uma nova flag que você pode colocar na classe para controlar essa fase
            estado_jogo.j1_reordenado = True 
        else:
            estado_jogo.jogador_jogador2 = novo_deck
            estado_jogo.j2_reordenado = True

    # 5. SEGUNDA BARREIRA DE ESPERA: Garante que o cálculo do vencedor 
    # só comece depois que AMBOS os jogadores terminarem de digitar a reordenação
    while True:
        with estado_jogo.lock_memoria:
            # Verifica se ambos os jogadores concluíram a Fase 2
            if getattr(estado_jogo, 'j1_reordenado', False) and getattr(estado_jogo, 'j2_reordenado', False):
                break
        time.sleep(0.1)    
          


def iniciar_servidor():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind(('127.0.0.1', 8888))
    servidor.listen(2)
    print("[SERVIDOR] Rodando na porta 8888. Aguardando os 2 jogadores...")
    jogadas = EstadoMemoriaCompartilhada()
    
    id_atual = 1
    while id_atual <= 2:
        conexao, endereco = servidor.accept()
        print(f"[SERVIDOR] Conexão aceita de {endereco}. Atribuído ID: {id_atual}")
        
        thread = threading.Thread(target=gerenciar_cliente, args=(conexao, id_atual, jogadas))
        thread.start()
        
        id_atual += 1

if __name__ == "__main__":
    iniciar_servidor()