import socket
from dataclasses import dataclass

from enum import Enum

class Jokenpo(Enum):
    PEDRA = 1
    PAPEL = 2
    TESOURA = 3

def reordena_jogadas(sua_jogada: str, jogada_adversaria: str) -> str:
    # Transforma a string de jogadas atual em uma lista para poder alterar as posições
    letras = list(sua_jogada.upper())
    
    while True:
        print("\n" + "="*40)
        print("          FASE 2: REORDENAÇÃO")
        print("="*40)
        print(f"Sua jogada atual  : {' '.join(letras)}")
        print(f"Jogada adversária : {' '.join(jogada_adversaria.upper())}")
        print("-"*40)
        print("Digite os índices (1 a 5) das cartas que deseja trocar de lugar.")
        print("Ou digite '0' no primeiro campo para finalizar a reordenação.")
        print("-"*40)
        
        try:
            # Pergunta a primeira carta
            idx1 = int(input("1ª carta a ser trocada (1-5): "))
            if idx1 == 0:
                print("[INFO] Reordenação finalizada pelo jogador.")
                break
                
            # Pergunta a segunda carta
            idx2 = int(input("2ª carta a ser trocada (1-5): "))
            
            # Validação: verifica se os índices estão no intervalo correto (1 a 5)
            if idx1 < 1 or idx1 > 5 or idx2 < 1 or idx2 > 5:
                print("[ERRO] Índices inválidos! Escolha números de 1 a 5.")
                continue
                
            if idx1 == idx2:
                print("[AVISO] Você escolheu a mesma carta. Nenhuma troca feita.")
                continue
            
            # A MÁGICA DA TROCA (SWAP):
            # Convertemos o índice de "humanos" (1-5) para o índice do Python (0-4)
            letras[idx1 - 1], letras[idx2 - 1] = letras[idx2 - 1], letras[idx1 - 1]
            print(f"[SUCESSO] Trocadas as posições {idx1} e {idx2}!")
            
        except ValueError:
            print("[ERRO] Entrada inválida! Por favor, digite apenas números inteiros.")
            
    # Converte a lista reordenada de volta para uma única string (ex: 'PTRRR')
    jogada_final = "".join(letras)
    return jogada_final


def scan_jogadas() -> list[Jokenpo]:
    '''
    Recebe as jogadas que o jogador pretende fazer.
    '''
    try:
        lst = []
        for i in range(5):
            jogada = int(input(f"""Selecione sua {i + 1}ª jogada\n
(1) Pedra (2) Papel (3) Tesoura
>> """))
            lst.append(Jokenpo(jogada))
    except Exception as e:
        print(f'erro: {e}')        
    return lst

def converte_para_string(lst: list[Jokenpo]) -> str:
    '''
    Converte uma lista *lst* de objetos Jokenpo em uma lista de strings,
    a fim de tornar as jogadas transmissíveis pelo socket.

    'R' -> Pedra
    'P' -> Papel
    'T' -> Tesoura 
    '''
    string = ''
    for x in lst:
        if x.name == 'PEDRA':
            string += 'R' # R de rock, para diferenciar de papel.
        elif x.name == 'PAPEL':
            string += 'P'    
        elif x.name == 'TESOURA':
            string += 'T'
    return string

def iniciar_cliente():
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    print("[CLIENTE] Tentando se conectar ao servidor...")
    cliente.connect(('127.0.0.1', 8888))
    print("[CLIENTE] Conectado com sucesso!")
    print("Digite suas mensagens abaixo. Digite 'sair' para encerrar.\n")
    
    try:
        while True:
            # Captura o que você digitar no terminal de forma dinâmica
            lst_jogadas = scan_jogadas()
            string_jogadas = converte_para_string(lst_jogadas) # Não é possível passar um lista pelo socket.
            
            # Envia a mensagem digitada
            cliente.send(string_jogadas.encode('utf-8'))
            
            jogada_adversaria = cliente.recv(1024).decode('utf-8')
            print(f"""[SERVIDOR]: Jogada do adversário -> {jogada_adversaria}
-> Sua jogada: {string_jogadas}""")

            jogada_reordenada = reordena_jogadas(string_jogadas, jogada_adversaria )
            cliente.send(jogada_reordenada.encode('utf-8'))          
           
            # Aguarda e exibe a resposta de confirmação do servidor
            resposta = cliente.recv(1024).decode('utf-8')
            print(f"[SERVIDOR]: {resposta}")
            
    except Exception as e:
        print(f"[ERRO] Conexão perdida com o servidor: {e}")
    finally:
        cliente.close()
        print("[CLIENTE] Conexão encerrada.")

if __name__ == "__main__":
    iniciar_cliente()