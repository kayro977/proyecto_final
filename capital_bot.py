import requests,time, os
import json
import pandas as pd

CST = ''
X_SECURITY_TOKEN = ''
with open('proyecto_final/config.json') as config_file:
    config = json.load(config_file)
    API_KEY = config['API_KEY']
    USERNAME = config['USERNAME']
    PASSWORD = config['PASSWORD']
    API_URL = 'https://demo-api-capital.backend-capital.com/'  



X_SECURITY_TOKEN = ''

#login para entrar a la cuenta
def login():
    global CST, X_SECURITY_TOKEN
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-CAP-API-KEY': API_KEY
    }

    data = {
        'identifier': USERNAME,
        'password': PASSWORD
    }

    response = requests.post(f'{API_URL}/api/v1/session', headers=headers, json=data)

    if response.status_code == 200:
        CST = response.headers.get('CST')
        X_SECURITY_TOKEN = response.headers.get('X-SECURITY-TOKEN')
        print("Login exitoso")
        print("CST:", CST)
        print("X-SECURITY-TOKEN:", X_SECURITY_TOKEN)
    else:
        print(" Error en login")
        print("Código:", response.status_code)
        print("Respuesta:", response.text)

#funcion para comprar acciones de apple
def comprar(epic='',cantidad=0):
    url = f'{API_URL}/api/v1/positions'
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-CAP-API-KEY': API_KEY,
        'CST': CST,
        'X-SECURITY-TOKEN': X_SECURITY_TOKEN
    }

    payload = {
        "epic": epic,
        "direction": "BUY",
        "size":cantidad,
        "orderType": "MARKET",
        "currencyCode": "USD",
        "forceOpen": True,
        "guaranteedStop": False,
        "timeInForce": "FILL_OR_KILL"
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code in [200, 201]:
        print("Compra realizada")
        print(json.dumps(response.json(), indent=2))
    else:
        print("Error al realizar la compra")
        print("codigo:{response.status_code}")


#funcion para vender acciones de apple
def vender(epic='',cantidad=0):
    url = f'{API_URL}/api/v1/positions'
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-CAP-API-KEY': API_KEY,
        'cst': CST,
        'X-SECURITY-TOKEN': X_SECURITY_TOKEN
    }
    payload = {
        "epic": epic,
        "direction": "SELL",
        "size": cantidad,
        "orderType": "MARKET",
        "currencyCode": "USD",
        "forceOpen": True,
        "guaranteedStop": False,
        "timeInForce": "FILL_OR_KILL"
    }
    response = requests.post(url,headers=headers,json=payload)
    if response.status_code in[200,201]:
        print("venta realizada con exito")
    else:
        print("Error al realizar la venta")
        print("codigo:{response.status_code}")


#funcion para obtener precio
def obtener_precio(epic=''):
    url =  f'{API_URL}/api/v1/prices/{epic}'
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-CAP-API-KEY': API_KEY,
        'CST': CST,
        'X-SECURITY-TOKEN': X_SECURITY_TOKEN
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        precios = data.get('prices', [])
        if precios:
            ultimo = precios[-1]  
            bid = ultimo['closePrice']['bid']
            ask = ultimo['closePrice']['ask']
            precio_medio = (bid + ask) / 2
            return precio_medio
        else:
            print("No hay precios disponibles")
    else:
        print("Error al obtener el precio")
        print("Código:", response.status_code)
        print("Respuesta:", response.text)


#mercado de criptomonedas a largo plazo
def analizar_criptomonedas(epic='', resolution='HOUR', num_velas=150):
    url = f"{API_URL}/api/v1/prices/{epic}?resolution={resolution}&max={num_velas}"
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-CAP-API-KEY': API_KEY,
        'CST': CST,
        'X-SECURITY-TOKEN': X_SECURITY_TOKEN
    }

    response = requests.get(url,headers=headers)
    if response.status_code in[200,201]:
        data = response.json()
        candles = data.get('prices', [])
        if len(candles) < 10:
            print("No hay suficientes velas para analizar")
            return
        
        # Crear DataFrame con los precios medios
        df = pd.DataFrame([{
            'timestamp': c['snapshotTime'],
            'ask': c['closePrice']['ask'],
            'bid': c['closePrice']['bid'],
            'mid': (c['closePrice']['bid'] + c['closePrice']['ask']) / 2,
            'volume': c['lastTradedVolume'],
        } for c in candles])

        df['ema_5'] = df['mid'].ewm(span=5, adjust=False).mean()
        df['ema_10'] = df['mid'].ewm(span=10, adjust=False).mean()
        df['sma_5'] = df['mid'].rolling(window=5).mean()
        df['sma_10'] = df['mid'].rolling(window=10).mean()

        # Tamaño del cuerpo de la vela
        df['body_size'] = abs(df['ask'] - df['bid'])

        # calcular momentum 
        df['momentum_3'] = df['mid'] - df['mid'].shift(3)
        df['momentum_10'] = df['mid'] - df['mid'].shift(10)
        df['momentum_20'] = df['mid'] - df['mid'].shift(20)
        # Últimos valores
        ultima = df.iloc[-1]
        ema_5_last = ultima['ema_5']
        ema_10_last = ultima['ema_10']
        sma_5_last = ultima['sma_5']
        sma_10_last = ultima['sma_10']
        vol_actual = ultima['volume']
        cuerpo_actual = ultima['body_size']

        
        # Promedios
        volumen_promedio = df['volume'].mean()
        cuerpo_promedio = df['body_size'].mean()

        # Análisis de volumen
        if vol_actual > volumen_promedio * 1.5: 
            if cuerpo_actual > cuerpo_promedio:
                print("✅ Movimiento fuerte con volumen alto: seguir la tendencia.")
                
            else:
                print("⚠️ Volumen alto pero vela pequeña: posible trampa o acumulación.")
           
        elif vol_actual < volumen_promedio * 0.5:
            print("😐 Volumen bajo: no operar.")
      
        else:
            print("🤔 Volumen neutro: operar solo si la tendencia es clara.")
       

        # Confirmación con medias móviles
        if ema_5_last > ema_10_last and sma_5_last > sma_10_last:
            print("📈 Es probable que suba, se recomienda COMPRAR.")
            precio_Actual = obtener_precio(epic='ETHUSD')
            print(f"Precio actual: {precio_Actual}")
            return "comprar"
        elif ema_5_last < ema_10_last and sma_5_last < sma_10_last:
            print("📉 Es probable que baje, se recomienda VENDER.")
            precio_Actual = obtener_precio(epic='ETHUSD')
            print(f"Precio actual: {precio_Actual}")
            return "vender"
        else:
            print("⏸️ No hay señal clara por medias móviles.")
            precio_Actual = obtener_precio(epic='ETHUSD')
            print(f"Precio actual: {precio_Actual}")
            return "ninguna"


#REGISTROS DEL BOT
def registro_bot(archivo='proyecto_final/registro.json', comprar=False, vender=False):
    # Si el archivo no existe, se crea con valores iniciales
    if not os.path.exists(archivo):
        data = {
            "veces_venta": 0,
            "veces_compra": 0,
            "ganancias": 0,
            "contador_ganancia_alcanzada":0,
            "contador_perdida":0
        }
        
    else:
        with open(archivo, 'r') as f:
            data = json.load(f)


    if comprar:
        data["veces_compra"] += 1
    if vender:
        data["veces_venta"] += 1



    with open(archivo, 'w') as f:
        json.dump(data, f, indent=4)



def bot():
    login()

    print("\n" + "=" * 60)
    print("🤖 BOT DE TRADING AUTOMÁTICO".center(60))
    print("=" * 60)

    user = input("🧑 Ingrese su usuario: ")
    print(f"\n👋 Bienvenido, amo {user}")

    posicion_abierta = None  # puede ser "comprar", "vender" o None
    precio_entrada = None

    print("\n" + "-" * 60)
    cantidad_compra = input("📦 ¿Cuántas acciones deseas comprar? ")
    epic = input("📊 ¿Qué activo deseas operar? (disponibles: ETHUSD o GOLD): ").upper()

    while True:
        if epic not in ['ETHUSD', 'GOLD']:
            print("Activo no válido. Por favor, elige entre ETHUSD o GOLD.")
            epic = input("¿Qué activo deseas operar? disponibles:ETHUSD O GOLD: ").upper()
        else:
            break


    #bucle principal del bot
    while True:
        try:
            resultado = analizar_criptomonedas(epic=epic)
            precio_actual = obtener_precio(epic=epic)

            if resultado == "comprar":
                if posicion_abierta == "vender":
                    # Cierra posición vendida comprando
                    print(f"Cerrando posición vendida, comprando {epic} a {precio_actual}")
                    comprar(f'{epic}', cantidad_compra)
                    posicion_abierta = None
                    precio_entrada = None
                if posicion_abierta != "comprar":
                    # Abre posición comprada
                    print(f"Comprando {epic} a {precio_actual}")
                    comprar(f'{epic}', cantidad_compra)
                    registro_bot(comprar=True)
                    posicion_abierta = "comprar"
                    precio_entrada = precio_actual
                else:
                    print("Ya tienes posición comprada, no haces nada.")

            elif resultado == "vender":
                if posicion_abierta == "comprar":
                    # Cierra posición comprada vendiendo
                    print(f"Cerrando posición comprada, vendiendo {epic} a {precio_actual}")
                    vender(f'{epic}', cantidad_compra)
                    posicion_abierta = None
                    precio_entrada = None
                if posicion_abierta != "vender":
                    # Abre posición vendida
                    print(f"Vendiendo {epic} a {precio_actual}")
                    vender(f'{epic}', cantidad_compra)
                    registro_bot(vender=True)
                    posicion_abierta = "vender"
                    precio_entrada = precio_actual
                else:
                    print("Ya tienes posición vendida, no haces nada.")

            else:
                print("No hay señal clara, no haces nada.")
                print(f"Precio actual: {precio_actual}")

            # Control de ganancia para cerrar operaciones con beneficio
            if posicion_abierta == "comprar" and precio_entrada is not None:
                ganancia = (precio_actual - precio_entrada) / precio_entrada * 100
                if ganancia >= 1:
                    print(f"Ganancia de {ganancia:.2f}% alcanzada, vendiendo para cerrar posición.")
                    vender(f'{epic}',cantidad_compra)
                    registro_bot(ganancia_alcanzada=True)
                    posicion_abierta = None
                    precio_entrada = None


            elif posicion_abierta == "vender" and precio_entrada is not None:
                ganancia = (precio_entrada - precio_actual) / precio_entrada * 100
                if ganancia >= 1:
                    print(f"Ganancia de {ganancia:.2f}% alcanzada, comprando para cerrar posición.")
                    comprar(f'{epic}',cantidad_compra)
                    registro_bot(ganancia_alcanzada=True)
                    posicion_abierta = None
                    precio_entrada = None
  
        except Exception as e:
            print(f"Error en el bot: {e}")

        time.sleep(10)
bot()