import Pyro5.api
Pyro5.config.SERIALIZER = 'marshal'
# Classe que representa o cliente do sistema de gestão de estoque
class StockManagementClient:

    def notify_replenishment(self, product_code):
        # Método chamado pelo servidor para notificar sobre a reposição de estoque
        print(f"Produto {product_code} atingiu o estoque mínimo. É necessário repor o estoque.")

    def notify_unsold_products(self, product):
        # Método chamado pelo servidor para enviar relatórios de produtos não vendidos
        print(f"Produto {product['name']} ({product['code']}) não foi vendido.")

# Configurar o cliente PyRO
if __name__ == "__main__":
    name = "NomeDoGestor"  # Nome do gestor de estoque
    public_key = "ChavePublicaDoGestor"  # Chave pública do gestor de estoque

    server_uri = "PYRONAME:stock_management_system"  # URI do servidor PyRO


    with Pyro5.api.Proxy(server_uri) as server:
        response = server.register_user(name,public_key)
        print(response)

    # O cliente agora está registrado no servidor e pronto para receber notificações e relatórios
