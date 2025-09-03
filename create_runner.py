runner_code = '''
import subprocess
import json

class Color:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Color.HEADER}{Color.BOLD}{{text}}{Color.END}")

def print_subheader(text):
    print(f"\n{Color.UNDERLINE}{{text}}{Color.END}")

def print_key_value(key, value, indent=1):
    tabs = "\t" * indent
    print(f"{tabs}{Color.BLUE}{{key}}:{Color.END} {{value}}")

def print_json_response(json_str):
    try:
        data = json.loads(json_str)
        for key, value in data.items():
            print_key_value(key, value)
    except (json.JSONDecodeError, AttributeError):
        print(f"\t{Color.YELLOW}{{json_str}}{Color.END}")

def run_tests():
    '''
    Runs the test commands and prints a formatted summary for each.
    '''
    print_header("--- Iniciando Prueba Visual del API del Smart Contract ---")

    commands = [
        ("Creando wallet para el usuario jorge...",
         "curl -s -X POST http://127.0.0.1:8000/api/blockchain/crear_wallet/ -H 'Content-Type: application/json' -d '{\"user_id\": 1, \"username\": \"jorge\"}'"),
        ("Creando wallet para el usuario daniel...",
         "curl -s -X POST http://127.0.0.1:8000/api/blockchain/crear_wallet/ -H 'Content-Type: application/json' -d '{\"user_id\": 2, \"username\": \"daniel\"}'"),
        ("Tokenizando la obra 'La Noche Estrellada' para el usuario jorge...",
         "curl -s -X POST http://127.0.0.1:8000/api/blockchain/tokenizar_cuadro/ -H 'Content-Type: application/json' -d '{\"user_id\": 1, \"cuadro_id\": 1, \"nombre_cuadro\": \"La Noche Estrellada\", \"artista\": \"Vincent van Gogh\", \"anio_creacion\": 1889, \"precio\": 1000000, \"propietario\": \"jorge\"}'"),
        ("Transfiriendo 50 tokens de 'La Noche Estrellada' de jorge a daniel...",
         "curl -s -X POST http://127.0.0.1:8000/api/blockchain/transferir_tokens/ -H 'Content-Type: application/json' -d '{\"from_user_id\": 1, \"to_user_id\": 2, \"cuadro_id\": 1, \"cantidad\": 50}'"),
        ("Consultando el balance de tokens de 'La Noche Estrellada' para el usuario jorge...",
         "curl -s http://127.0.0.1:8000/api/blockchain/consultar_balance/1/1/",
        ("Consultando el balance de tokens de 'La Noche Estrellada' para el usuario daniel...",
         "curl -s http://127.0.0.1:8000/api/blockchain/consultar_balance/2/1/",
        ("Consultando el historial de transacciones de 'La Noche Estrellada'...",
         "curl -s http://127.0.0.1:8000/api/blockchain/historial_transacciones/1/"
    )]

    for description, command in commands:
        print_subheader(description)
        result = subprocess.run(command, shell=True, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"\t{Color.RED}Error al ejecutar el comando.{Color.END}")
            print(f"\t{{result.stderr}}")
        else:
            print_json_response(result.stdout)

    print_header("--- Prueba Finalizada ---")


if __name__ == "__main__":
    run_tests()

with open("visual_test_runner.py", "w") as f:
    f.write(runner_code.replace("'''", '"""'))