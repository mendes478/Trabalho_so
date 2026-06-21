import socket
import threading
import time
from dataclasses import dataclass
from cliente1 import Jokenpo

class EstadoMemoriaCompartilhada():
    jogadas_jogador1: str
    jogador_jogador2: str
    fase_jogador1: int
    fase_jogador2: int
    j1_pronto: bool
    j2_pronto: bool
    lock_memoria: threading.Lock

    def __init__(self):
        self.jogadas_jogador1 = ""
        self.jogadas_jogador2 = ""
        self.fase_jogador1 = 1
        self.fase_jogador2 = 1
        self.j1_pronto = False
        self.j2_pronto = False
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
                else:
                    estado_jogo.jogador_jogador2 = dados # Mantendo o nome da sua classe anterior
                
                atualiza_fase(estado_jogo, id_jogador)
                deixa_pronto(estado_jogo, id_jogador)

            # 2. BARREIRA DE ESPERA: Ambas as threads param aqui e esperam as duas ficarem prontas
            while True:
                with estado_jogo.lock_memoria:
                    if estado_jogo.j1_pronto and estado_jogo.j2_pronto:
                        break # Condição atendida! Sai do laço de espera
                time.sleep(0.1) # Evita o uso excessivo de CPU enquanto aguarda

            # 3. PROCESSAMENTO EXCLUSIVO DA THREAD 1
            # Apenas a thread do Jogador 1 vai calcular o vencedor para evitar duplicidade
            if id_jogador == 1:
                # Aqui você roda a lógica de cálculo
                resultado = computar_vencedor(estado_jogo.jogadas_jogador1, estado_jogo.jogador_jogador2)
                
                # Guarda o resultado string final na memória compartilhada (você pode adicionar esse campo na classe)
                with estado_jogo.lock_memoria:
                    estado_jogo.resultado_final = resultado
                    estado_jogo.processamento_concluido = True

            # 4. SEGUNDA BARREIRA DE ESPERA (Para o Jogador 2 esperar o cálculo do Jogador 1)
            while True:
                with estado_jogo.lock_memoria:
                    # Se você inicializar processamento_concluido como False na dataclass
                    if getattr(estado_jogo, 'processamento_concluido', False):
                        break
                time.sleep(0.1)

            # 5. ENVIO DOS RESULTADOS SINCRONIZADOS
            # Agora que o cálculo foi feito de forma limpa, envia a resposta correta para cada um
            with estado_jogo.lock_memoria:
                resposta = estado_jogo.resultado_final
            
            conexao.send(resposta.encode('utf-8'))
            
            # 6. LIMPEZA DE FLAGS PARA A PRÓXIMA RODADA (Se o jogo continuar)
            with estado_jogo.lock_memoria:
                if id_jogador == 1:
                    estado_jogo.j1_pronto = False
                else:
                    estado_jogo.j2_pronto = False
                    estado_jogo.processamento_concluido = False

    except Exception as e:
        print(f"[ERRO] Exceção na thread do Jogador {id_jogador}: {e}")
    finally:
        conexao.close()

def atualiza_fase(estado: EstadoMemoriaCompartilhada, id_jogador):
    if id_jogador == 1:
        estado.fase_jogador1 += 1
    elif id_jogador == 2:
        estado.fase_jogador2 += 2    

def deixa_pronto(estado: EstadoMemoriaCompartilhada, id_jogador):
    if id_jogador == 1:
        estado.j1_pronto = True
    elif id_jogador == 2:
        estado.j2_pronto = True


def computar_vencedor(jogadas_j1, jogadas_j2):
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
        return f"Resultado: Jogador 1 Venceu! Placar: {pontos_j1}x{pontos_j2}"
    elif pontos_j2 > pontos_j1:
        return f"Resultado: Jogador 2 Venceu! Placar: {pontos_j2}x{pontos_j1}"
    else:
        return f"Resultado: Empate Geral! Placar: {pontos_j1}x{pontos_j2}"
          


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