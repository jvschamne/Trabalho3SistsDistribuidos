import Pyro5.api
import hashlib
import datetime

Pyro5.config.SERIALIZER = 'marshal'
# Classe que representa um produto no estoque
class Product:
    def __init__(self, code, name, description, quantity, price, min_stock):
        self.code = code
        self.name = name
        self.description = description
        self.quantity = quantity
        self.price = price
        self.min_stock = min_stock
        self.movements = []

    def add_entry(self, quantity):
        self.quantity += quantity
        self.movements.append((datetime.datetime.now(), "entrada", quantity))

    def add_exit(self, quantity):
        if self.quantity >= quantity:
            self.quantity -= quantity
            self.movements.append((datetime.datetime.now(), "saída", quantity))

    def get_stock_status(self):
        return {
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "quantity": self.quantity,
            "price": self.price,
            "min_stock": self.min_stock,
        }

# Classe que representa um usuário do sistema
class User:
    def __init__(self, name, public_key):
        self.name = name
        self.public_key = public_key

# Classe que representa o sistema de gestão de estoque
class StockManagementSystem:
    def __init__(self):
        self.users = {}  # Dicionário de usuários (nome do usuário -> objeto do usuário)
        self.products = {}  # Dicionário de produtos (código do produto -> objeto do produto)
        self.clients = {}  # Dicionário de clientes (nome do cliente -> objeto do cliente)
    @Pyro5.api.expose
    def register_user(self, name, public_key):
        if name not in self.users:
            user = User(name, public_key)
            self.users[name] = user
            return f"Usuário {name} registrado com sucesso."
        else:
            return f"Usuário {name} já está registrado."

    def add_product(self, code, name, description, quantity, price, min_stock):
        if code not in self.products:
            product = Product(code, name, description, quantity, price, min_stock)
            self.products[code] = product
            return f"Produto {name} ({code}) adicionado ao estoque."
        else:
            return f"Produto {name} ({code}) já está no estoque."

    def record_entry(self, code, user_name, quantity, signature):
        if user_name in self.users:
            user = self.users[user_name]
            if code in self.products:
                product = self.products[code]
                # Verificar a assinatura digital com a chave pública do usuário
                if self.verify_signature(signature, user.public_key):
                    product.add_entry(quantity)
                    # Verificar se a quantidade após a entrada atingiu o estoque mínimo
                    if product.quantity <= product.min_stock:
                        self.notify_replenishment(user_name, product)
                    return f"Entrada de {quantity} unidades de {product.name} registrada."
                else:
                    return "Assinatura digital inválida."
            else:
                return "Produto não encontrado."
        else:
            return "Usuário não encontrado."

    def record_exit(self, code, user_name, quantity, signature):
        if user_name in self.users:
            user = self.users[user_name]
            if code in self.products:
                product = self.products[code]
                # Verificar a assinatura digital com a chave pública do usuário
                if self.verify_signature(signature, user.public_key):
                    product.add_exit(quantity)
                    return f"Saída de {quantity} unidades de {product.name} registrada."
                else:
                    return "Assinatura digital inválida."
            else:
                return "Produto não encontrado."
        else:
            return "Usuário não encontrado."

    def verify_signature(self, signature, public_key):
        # Implemente a verificação da assinatura digital aqui
        # Use a chave pública para verificar a assinatura
        # Retorne True se a assinatura for válida, caso contrário, retorne False
        return True
    @Pyro5.api.expose
    def generate_stock_report(self):
        # Implemente a geração de relatórios aqui
        # Isso pode incluir produtos em estoque, movimentação de estoque e produtos sem saída
        pass
    @Pyro5.api.expose 
    def notify_replenishment(self, user_name, product):
        # Método para notificar o gestor quando um produto atinge o estoque mínimo
        if user_name in self.clients:
            client = self.clients[user_name]
            client.notify_replenishment(product.code)
    @Pyro5.api.expose
    def notify_unsold_products(self):
        # Método para enviar relatórios periódicos sobre produtos não vendidos
        for product in self.products.values():
            if product.quantity == 0:
                for user_name in self.clients:
                    client = self.clients[user_name]
                    client.notify_unsold_products(product)

    def __reduce__(self):
        return (self.__class__, (self.name, self.public_key))

# Configurar o servidor PyRO
if __name__ == "__main__":
    daemon = Pyro5.api.Daemon()
    ns = Pyro5.api.locate_ns()
    uri = daemon.register(StockManagementSystem)
    ns.register("stock_management_system", uri)
    print("Servidor PyRO pronto.")
    daemon.requestLoop()