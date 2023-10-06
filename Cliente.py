import Pyro5.api
import threading
import inquirer

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes

#Pyro5.api.config.SERIALIZER = 'marshal'

# Classe que representa o cliente do sistema de gestão de estoque
class StockManagementClient:

    @Pyro5.api.expose 
    def notify_replenishment(self, product_code):
        # Método chamado pelo servidor para notificar sobre a reposição de estoque
        print(f"> Notificação: Produto de código {product_code} está abaixo do estoque mínimo. É necessário repor o estoque.")

    @Pyro5.api.expose 
    def notify_unsold_products(self, product):
        # Método chamado pelo servidor para enviar relatórios de produtos não vendidos
        print(f"> Notificação: {product['name']} ({product['code']}) não foi vendido.")


def keysGenerator():

    # Gerar um par de chaves RSA
    private_key = rsa.generate_private_key(
        public_exponent=65537,  # Exponente público padrão (Fermat F4)
        key_size=2048,          # Tamanho da chave (pode ser 2048, 3072, 4096, etc.)
        backend=default_backend()
    )

    # Obter a chave pública correspondente
    public_key = private_key.public_key()

    # Serializar as chaves para armazenamento ou transmissão
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # Salvar as chaves em arquivos
    with open("private_key.pem", "wb") as f:
        f.write(private_key_pem)

    with open("public_key.pem", "wb") as f:
        f.write(public_key_pem)

    print("Chaves geradas e salvas com sucesso!")
    return [private_key_pem, public_key_pem, private_key]


# Função para assinar uma mensagem com a chave privada
def sign_message(message, private_key):
    signature = private_key.sign(
        message.encode('utf-8'),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return signature


# Configurar o cliente PyRO
if __name__ == "__main__":

    # Registrar objeto cliente
    daemon = Pyro5.api.Daemon()
    uri = daemon.register(StockManagementClient())

    # Gerar chaves
    keys = keysGenerator()
    private_key = keys[0]
    public_key = keys[1]
    pk = keys[2]

    # Pegar objeto do servidor

    servidor_nomes = Pyro5.api.locate_ns()
    server_uri = servidor_nomes.lookup("stock_management_system")


    server = Pyro5.api.Proxy(server_uri) 



    #name = "NomeDoGestor2"  # Nome do gestor de estoque
 
    name = input("Qual o seu nome? ")
    response = server.register_user(name, public_key, uri)
    print(response)
    # O cliente agora está registrado no servidor e pronto para receber notificações e relatórios
        


    #colocar request loop dentro de uma thread
    threading.Thread(target=daemon.requestLoop).start()

    message = name
    signature = sign_message(message, pk)
    
    while(True):
        questions = [
                inquirer.List('action', message="Qual acao deseja tomar?", 
                            choices=['Entrada de produtos', 'Saida de produtos', 'Relatorio'],)

        ]
        answer = inquirer.prompt(questions)
        print(answer)
        if(answer['action'] == 'Entrada de produtos'):
                print('Entrada de produtos')
                server.record_entry(name, 1, 'bulacha', 'Bolacha Waffer', 10, 5.5, 50, signature)
        elif(answer['action'] == 'Saida de produtos'):
                print('Saida de produtos')
                server.record_exit(1, name, 10, signature)
        elif(answer['action'] == 'Relatorio'):
                print('Relatorio')
                questions2 = [
                inquirer.List('action2', message="Qual acao deseja tomar?", 
                            choices=['Produtos em estoque', 'Fluxo de movimentação', 'Lista de produtos sem saída'])

                ]
                answer = inquirer.prompt(questions2)
                if(answer['action2']== 'Produtos em estoque'):
                    print('Produtos em estoque')
                    produtosEmEstoque= server.generate_stock_report('Produtos em estoque')
                    for product in produtosEmEstoque:
                        print(f"Produto {product['name']} ({product['code']}) está acima do estoque mínimo possuindo {product['quantity']} unidades em estoque")

                elif(answer['action2']== 'Fluxo de movimentação'):
                        print('Fluxo de movimentação')
                        fluxoMov= server.generate_stock_report('Fluxo de movimentação')
                        print("Movimentos:")
                        for product in fluxoMov:
                            for movement in product['movements']:
                                print(f"Produto {product['name']} ({product['code']})  - Tipo: {movement['type']}, Quantidade: {movement['quantity']}, Hora: {movement['time']}")

                elif(answer['action2']== 'Lista de produtos sem saída'):
                        print('Lista de produtos sem saída')
                        prodSemSaida = server.generate_stock_report('Lista de produtos sem saída')
                        for product in prodSemSaida :
                            print(f"Produto {product['name']} ({product['code']}) não teve movimentos de saída até 2 minutos atrás.")
