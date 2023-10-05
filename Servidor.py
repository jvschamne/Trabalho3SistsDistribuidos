import Pyro5.api
import datetime
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
import base64
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

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
    def __init__(self, name, public_key, client_object):
        self.name = name
        self.public_key = public_key
        self.client_object = client_object

# Classe que representa o sistema de gestão de estoque
class StockManagementSystem:
    def __init__(self):
        self.users = {}  # Dicionário de usuários (nome do usuário -> objeto do usuário)
        self.products = {}  # Dicionário de produtos (código do produto -> objeto do produto)
        self.clients = {}  # Dicionário de clientes (nome do cliente -> objeto do cliente)
    @Pyro5.api.expose
    def register_user(self, name, public_key, client_object):
        print(public_key)
        print("Usuarios cadastrados: ", self.users)
        print("Name:", name)
        if name not in self.users:
            user = User(name, public_key, client_object)
            self.users[name] = user
            print(self.users[name], self.users[name].name, self.users, self.users[name].public_key)
            return f"Usuário {name} registrado com sucesso."
        else:
            print("else")
            return f"Usuário {name} já está registrado."


    @Pyro5.api.expose
    def record_entry(self, user_name, code, name, description, quantity, price, min_stock, signature):
        if user_name in self.users:
            user = self.users[user_name]
            if code in self.products:
                print("Produto adicionado")
                product = self.products[code]
                # Verificar a assinatura digital com a chave pública do usuário
                if self.verify_signature(signature, user.public_key, user_name):
                    print("Assinatura digital válida.")
                    product.add_entry(quantity)
                    # Verificar se a quantidade após a entrada atingiu o estoque mínimo
                    if product.quantity <= product.min_stock:
                        self.notify_replenishment(user_name, product)
                    return f"Entrada de {quantity} unidades de {product.name} registrada."
                else:
                    print("Assinatura digital inválida.")
                    return "Assinatura digital inválida."
            else:
                print(name, code)
                product = Product(code, name, description, quantity, price, min_stock)
                self.products[code] = product
                self.products[code].add_entry(quantity)
                return f"Produto {name} ({code}) adicionado ao estoque."

        else:
            return "Usuário não encontrado."

    def record_exit(self, code, user_name, quantity, signature):
        if user_name in self.users:
            user = self.users[user_name]
            if code in self.products:
                product = self.products[code]
                # Verificar a assinatura digital com a chave pública do usuário
                if self.verify_signature(signature, user.public_key, user_name):
                    product.add_exit(quantity)
                    return f"Saída de {quantity} unidades de {product.name} registrada."
                else:
                    return "Assinatura digital inválida."
            else:
                return "Produto não encontrado."
        else:
            return "Usuário não encontrado."

    def verify_signature(self, signature, public_key, message):
        # Implemente a verificação da assinatura digital aqui
        # Use a chave pública para verificar a assinatura
        # Retorne True se a assinatura for válida, caso contrário, retorne False

        # Decodifique a base64
        public_key_bytes = base64.b64decode(public_key)

        # Carregue a chave pública PEM
        #public_key = serialization.load_pem_public_key(public_key_bytes, backend=default_backend())

        print('tenta verificar assinatura:', message)
        print(public_key)
        try:
            public_key.verify(
                signature,
                message.encode('utf-8'),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True  # Assinatura válida
        except Exception as error:
            print(error)
            return False  # Assinatura inválida



        return True
    @Pyro5.api.expose
    def generate_stock_report(self, report_type):
        if report_type == 'Produtos em estoque':
                emEstoque = []
                for product in self.products.values():
                     if product.quantity > product.min_stock:
                        product_info = {
                            "code": product.code,
                            "name": product.name,
                            "quantity": product.quantity
                            }
                        emEstoque.append(product_info)
                return emEstoque
    
        elif report_type == 'Fluxo de movimentação':
                current_time = datetime.datetime.now()
                time = current_time - datetime.timedelta(minutes=1)
           
    
                fluxoMov = []
                for product in self.products.values():
                     if product.quantity > product.min_stock:
                        product_info = {
                            "code": product.code,
                            "name": product.name,
                            "movements": []
                            }

                # Filtrar os movimentos que ocorreram até 2 minutos atrás
                for movement_time, movement_type, movement_quantity in product.movements:
                    if movement_time >= time:
                        product_info["movements"].append({
                            "time": movement_time,
                            "type": movement_type,
                            "quantity": movement_quantity
                             })

                fluxoMov.append(product_info)
                return  fluxoMov
                
        elif report_type == 'Lista de produtos sem saída':
                current_time = datetime.datetime.now()
                two_minutes_ago = current_time - datetime.timedelta(minutes=1)

                unsold_products = []

                for product in self.products.values():
                    has_exit_movements = any(
                        movement_time >= two_minutes_ago and movement_type == "saída"
                        for movement_time, movement_type, _ in product.movements
                    )

                    if not has_exit_movements:
                        unsold_products.append({
                            "code": product.code,
                            "name": product.name
                        })

        return unsold_products

    @Pyro5.api.expose 
    def notify_replenishment(self, user_name, product):
        # Método para notificar o gestor quando um produto atinge o estoque mínimo
        print("produto fora de esoque")
        print(user_name, self.users)
        if user_name in self.users:
            print("user in clientes")
            client = self.users[user_name]
            print(client.client_object)

            auxObject = Pyro5.api.Proxy(client.client_object)
            print("ok1")
            print(auxObject)
            auxObject.notify_replenishment(product.code)
            print("ok3")
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
    uri = daemon.register(StockManagementSystem())
    ns.register("stock_management_system", uri)
    print("Servidor PyRO pronto.")
    daemon.requestLoop()
