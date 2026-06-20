import socket
import threading

def gerenciar_cliente(conexao, id_jogador):
    print(f"[THREAD] Iniciada para o Jogador {id_jogador}")
    try:
        while True:
            # Recebe os dados do cliente
            dados = conexao.recv(1024).decode('utf-8')
            
            # Se o cliente fechar a conexão de forma limpa ou digitar 'sair'
            if not dados or dados.lower() == 'sair':
                print(f"[SERVIDOR] Jogador {id_jogador} solicitou desconexão ou saiu.")
                break
                
            print(f"[JOGADOR {id_jogador}]: {dados}")
            
            # Devolve uma confirmação para o cliente saber que chegou lá
            resposta = f"Recebido: '{dados}'"
            conexao.send(resposta.encode('utf-8'))

    except Exception as e:
        print(f"[ERRO] Falha na comunicação com o Jogador {id_jogador}: {e}")
    finally:
        conexao.close()
        print(f"[THREAD] Finalizada para o Jogador {id_jogador}")

def iniciar_servidor():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind(('127.0.0.1', 8888))
    servidor.listen(2)
    print("[SERVIDOR] Rodando na porta 8888. Aguardando os 2 jogadores...")
    
    id_atual = 1
    while id_atual <= 2:
        conexao, endereco = servidor.accept()
        print(f"[SERVIDOR] Conexão aceita de {endereco}. Atribuído ID: {id_atual}")
        
        thread = threading.Thread(target=gerenciar_cliente, args=(conexao, id_atual))
        thread.start()
        
        id_atual += 1

if __name__ == "__main__":
    iniciar_servidor()