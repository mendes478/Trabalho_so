import socket
from dataclasses import dataclass

from enum import Enum

class Jokenpo(Enum):
    PEDRA = 1
    PAPEL = 2
    TESOURA = 3

def scan_jogadas() -> list[Jokenpo]:
    '''
    Recebe as jogadas que o jogador pretende fazer.
    '''
    lst = []
    for i in range(5):
        jogada = int(input(f"""Selecione sua {i + 1}ª jogada\n
(1) Pedra (2) Papel (3) Tesoura
>> """))
        lst.append(Jokenpo(jogada))
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