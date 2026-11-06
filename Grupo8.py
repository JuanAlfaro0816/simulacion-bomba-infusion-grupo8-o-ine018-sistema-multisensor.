
# ==============================================================
# SIMULACIÓN Y VALIDACIÓN DEL SISTEMA MULTISENSOR - GRUPO 8
# Bomba de infusión: caudal, presión y corriente del motor
#
# RESULTADOS GENERADOS:
# 1. Figura de caudal.
# 2. Figura de presión.
# 3. Figura de corriente.
# 4. Figura comparativa de tiempos de detección.
# 5. Tabla de resultados.
# 6. Indicadores cuantificables.
# 7. Archivos CSV y TXT.
#
# IMPORTANTE:
# Las señales son simuladas matemáticamente.
# No representan mediciones de una bomba real.
# ==============================================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# ==============================================================
# 1. PARÁMETROS GENERALES
# ==============================================================

carpeta = Path("resultados_grupo8")
carpeta.mkdir(exist_ok=True)

duracion = 120.0
inicio_anomalia = 60.0
paso = 0.1
tiempo_confirmacion = 2.0

# Valores de referencia
caudal_programado = 120.0       # mL/h
factor_goteo = 60.0             # gotas/mL
presion_inicial = 30.0          # mmHg
corriente_inicial = 0.30        # A

# Umbrales del sistema multisensor
umbral_caudal = caudal_programado * 0.80
umbral_presion = presion_inicial + 20.0
umbral_corriente = corriente_inicial * 1.10

# Umbral del sistema convencional
umbral_convencional = 100.0     # mmHg

tiempo = np.round(
    np.arange(0, duracion + paso / 2, paso), 2
)

tiempo_evento = tiempo - inicio_anomalia
x = np.maximum(tiempo_evento, 0.0)


# ==============================================================
# 2. FUNCIONES AUXILIARES
# ==============================================================

def rampa_lineal(x, inicial, final, duracion):
    """Genera una variación lineal entre dos valores."""
    proporcion = np.clip(x / duracion, 0, 1)
    return inicial + (final - inicial) * proporcion


def detectar_instante(condicion, tiempos, permanencia):
    """
    Calcula el primer instante en el que una condición
    permanece activa durante el tiempo establecido.
    """
    inicio = None

    for k, cumple in enumerate(condicion):

        if cumple:

            if inicio is None:
                inicio = tiempos[k]

            if tiempos[k] - inicio >= permanencia - 1e-9:
                return float(tiempos[k])

        else:
            inicio = None

    return None


def tiempo_relativo(instante):
    """Convierte el tiempo absoluto a tiempo desde la anomalía."""

    if instante is None:
        return None

    return round(instante - inicio_anomalia, 1)


# ==============================================================
# 3. CONSTRUCCIÓN DE LOS ESCENARIOS SIMULADOS
# ==============================================================

escenarios = {}

# --------------------------------------------------------------
# ESCENARIO 1: FUNCIONAMIENTO NORMAL
# --------------------------------------------------------------

escenarios["Funcionamiento normal"] = {
    "caudal_sensor": np.full_like(
        tiempo, caudal_programado
    ),
    "caudal_fisico": np.full_like(
        tiempo, caudal_programado
    ),
    "presion": np.full_like(
        tiempo, presion_inicial
    ),
    "corriente": np.full_like(
        tiempo, corriente_inicial
    )
}


# --------------------------------------------------------------
# ESCENARIO 2: OBSTRUCCIÓN PARCIAL
# --------------------------------------------------------------

# A los 3 segundos:
# Caudal = 95 mL/h, inferior a 96 mL/h.
# Presión = 51 mmHg, superior a 50 mmHg.

caudal_parcial = np.where(
    x <= 3.0,
    rampa_lineal(x, 120.0, 95.0, 3.0),
    np.where(
        x <= 5.0,
        rampa_lineal(x - 3.0, 95.0, 60.0, 2.0),
        60.0
    )
)

presion_parcial = np.where(
    x <= 3.0,
    rampa_lineal(x, 30.0, 51.0, 3.0),
    np.where(
        x <= 5.0,
        rampa_lineal(x - 3.0, 51.0, 65.0, 2.0),
        65.0
    )
)

corriente_parcial = np.where(
    tiempo < inicio_anomalia,
    0.30,
    0.31
)

caudal_parcial = np.where(
    tiempo < inicio_anomalia,
    120.0,
    caudal_parcial
)

presion_parcial = np.where(
    tiempo < inicio_anomalia,
    30.0,
    presion_parcial
)

escenarios["Obstrucción parcial"] = {
    "caudal_sensor": caudal_parcial,
    "caudal_fisico": caudal_parcial.copy(),
    "presion": presion_parcial,
    "corriente": corriente_parcial
}


# --------------------------------------------------------------
# ESCENARIO 3: OBSTRUCCIÓN COMPLETA
# --------------------------------------------------------------

# El caudal disminuye hasta 0 mL/h en 1 segundo.
# La presión alcanza 51 mmHg en 1 segundo.
# La presión alcanza 100 mmHg a los 9 segundos.
# La corriente aumenta hasta 0.34 A como supuesto didáctico.

caudal_completa = rampa_lineal(
    x, 120.0, 0.0, 1.0
)

presion_completa = np.where(
    x <= 1.0,
    rampa_lineal(x, 30.0, 51.0, 1.0),
    np.where(
        x <= 9.0,
        rampa_lineal(x - 1.0, 51.0, 100.0, 8.0),
        np.where(
            x <= 12.0,
            rampa_lineal(x - 9.0, 100.0, 125.0, 3.0),
            125.0
        )
    )
)

corriente_completa = rampa_lineal(
    x, 0.30, 0.34, 1.0
)

caudal_completa = np.where(
    tiempo < inicio_anomalia,
    120.0,
    caudal_completa
)

presion_completa = np.where(
    tiempo < inicio_anomalia,
    30.0,
    presion_completa
)

corriente_completa = np.where(
    tiempo < inicio_anomalia,
    0.30,
    corriente_completa
)

escenarios["Obstrucción completa"] = {
    "caudal_sensor": caudal_completa,
    "caudal_fisico": caudal_completa.copy(),
    "presion": presion_completa,
    "corriente": corriente_completa
}


# --------------------------------------------------------------
# ESCENARIO 4: POSIBLE FALLA DEL SENSOR ÓPTICO
# --------------------------------------------------------------

# El caudal físico permanece en 120 mL/h.
# La lectura del sensor óptico disminuye.
# La presión y la corriente permanecen normales.

lectura_optica = np.where(
    x < 1.0,
    rampa_lineal(x, 120.0, 96.0, 1.0),
    np.where(
        x <= 3.0,
        rampa_lineal(x - 1.0, 90.0, 0.0, 2.0),
        0.0
    )
)

lectura_optica = np.where(
    tiempo < inicio_anomalia,
    120.0,
    lectura_optica
)

escenarios["Falla del sensor óptico"] = {
    "caudal_sensor": lectura_optica,
    "caudal_fisico": np.full_like(
        tiempo, caudal_programado
    ),
    "presion": np.full_like(
        tiempo, presion_inicial
    ),
    "corriente": np.full_like(
        tiempo, corriente_inicial
    )
}


# ==============================================================
# 4. LÓGICA DE DETECCIÓN
# ==============================================================

resultados = {}

for nombre, senales in escenarios.items():

    caudal = senales["caudal_sensor"]
    presion = senales["presion"]
    corriente = senales["corriente"]

    # SISTEMA CONVENCIONAL
    # Se activa cuando la presión alcanza 100 mmHg.

    condicion_convencional = (
        presion >= umbral_convencional
    )

    instante_convencional = detectar_instante(
        condicion_convencional,
        tiempo,
        0.0
    )

    # SISTEMA MULTISENSOR
    # Se necesita caudal bajo y presión alta simultáneamente.

    condicion_obstruccion = (
        (caudal < umbral_caudal) &
        (presion > umbral_presion)
    )

    instante_obstruccion = detectar_instante(
        condicion_obstruccion,
        tiempo,
        tiempo_confirmacion
    )

    # POSIBLE FALLA DEL SENSOR ÓPTICO
    # Caudal bajo, presión normal y corriente normal.

    condicion_falla = (
        (caudal < umbral_caudal) &
        (presion <= umbral_presion) &
        (corriente <= umbral_corriente)
    )

    instante_falla = detectar_instante(
        condicion_falla,
        tiempo,
        tiempo_confirmacion
    )

    if nombre == "Falla del sensor óptico":

        instante_multisensor = instante_falla
        clasificacion = "Posible falla del sensor óptico"

    elif nombre in [
        "Obstrucción parcial",
        "Obstrucción completa"
    ]:

        instante_multisensor = instante_obstruccion
        clasificacion = "Probable obstrucción"

    else:

        instante_multisensor = None
        clasificacion = "Sin anomalía"

    resultados[nombre] = {
        "convencional": tiempo_relativo(
            instante_convencional
        ),
        "multisensor": tiempo_relativo(
            instante_multisensor
        ),
        "clasificacion": clasificacion
    }


# ==============================================================
# 5. TABLA DE RESULTADOS
# ==============================================================

tabla = pd.DataFrame([
    {
        "Escenario": nombre,

        "Sistema convencional (s)": (
            "No detecta"
            if datos["convencional"] is None
            else datos["convencional"]
        ),

        "Sistema multisensor (s)": (
            "No detecta"
            if datos["multisensor"] is None
            else datos["multisensor"]
        ),

        "Clasificación": datos["clasificacion"]
    }

    for nombre, datos in resultados.items()
])

print("\n==============================================")
print("RESULTADOS DE LA SIMULACIÓN - GRUPO 8")
print("==============================================")

print(tabla.to_string(index=False))


# ==============================================================
# 6. INDICADORES CUANTIFICABLES
# ==============================================================

tiempo_convencional = resultados[
    "Obstrucción completa"
]["convencional"]

tiempo_multisensor = resultados[
    "Obstrucción completa"
]["multisensor"]

reduccion = (
    (tiempo_convencional - tiempo_multisensor)
    / tiempo_convencional
) * 100

diferencia = (
    tiempo_convencional - tiempo_multisensor
)

# Cobertura de los tres escenarios de anomalía.

anomalias = [
    "Obstrucción parcial",
    "Obstrucción completa",
    "Falla del sensor óptico"
]

detectados_convencional = sum(
    resultados[n]["convencional"] is not None
    for n in anomalias
)

detectados_multisensor = sum(
    resultados[n]["multisensor"] is not None
    for n in anomalias
)

cobertura_convencional = (
    detectados_convencional / 3
) * 100

cobertura_multisensor = (
    detectados_multisensor / 3
) * 100

print("\nINDICADORES CUANTIFICABLES")

print(
    f"Reducción del tiempo de detección: "
    f"{reduccion:.1f} %"
)

print(
    f"Diferencia de tiempo: "
    f"{diferencia:.1f} segundos"
)

print(
    f"Cobertura convencional: "
    f"{detectados_convencional}/3 = "
    f"{cobertura_convencional:.1f} %"
)

print(
    f"Cobertura multisensor: "
    f"{detectados_multisensor}/3 = "
    f"{cobertura_multisensor:.1f} %"
)


# ==============================================================
# 7. EXPORTAR DATOS A CSV
# ==============================================================

filas = []

for nombre, senales in escenarios.items():

    for k in range(len(tiempo)):

        filas.append({
            "Escenario": nombre,
            "Tiempo_s": tiempo[k],

            "Caudal_sensor_mL_h":
                senales["caudal_sensor"][k],

            "Caudal_fisico_simulado_mL_h":
                senales["caudal_fisico"][k],

            "Presion_mmHg":
                senales["presion"][k],

            "Corriente_A":
                senales["corriente"][k]
        })

df = pd.DataFrame(filas)

df.to_csv(
    carpeta / "datos_simulados_grupo8.csv",
    index=False,
    encoding="utf-8-sig"
)

tabla.to_csv(
    carpeta / "resumen_deteccion_grupo8.csv",
    index=False,
    encoding="utf-8-sig"
)


# Crear resumen de texto

with open(
    carpeta / "resumen_simulacion_grupo8.txt",
    "w",
    encoding="utf-8"
) as archivo:

    archivo.write("SIMULACIÓN DIDÁCTICA - GRUPO 8\n\n")
    archivo.write(
        "Los resultados son simulados, no mediciones reales.\n\n"
    )

    archivo.write(tabla.to_string(index=False))

    archivo.write("\n\nINDICADORES\n")

    archivo.write(
        f"Reducción del tiempo: {reduccion:.1f} %\n"
    )

    archivo.write(
        f"Diferencia: {diferencia:.1f} segundos\n"
    )

    archivo.write(
        f"Cobertura convencional: "
        f"{cobertura_convencional:.1f} %\n"
    )

    archivo.write(
        f"Cobertura multisensor: "
        f"{cobertura_multisensor:.1f} %\n"
    )

    archivo.write(
        "\nLa cobertura corresponde únicamente "
        "a los escenarios programados.\n"
    )


# ==============================================================
# 8. FIGURA 5.1: CAUDAL
# ==============================================================

plt.figure(figsize=(11, 6))

for nombre, senales in escenarios.items():

    plt.plot(
        tiempo,
        senales["caudal_sensor"],
        linewidth=2,
        label=nombre
    )

# Comparación entre lectura óptica y caudal físico supuesto.

plt.plot(
    tiempo,
    escenarios["Falla del sensor óptico"]["caudal_fisico"],
    linestyle="--",
    linewidth=1.8,
    label="Caudal físico supuesto (falla óptica)"
)

plt.axvline(
    inicio_anomalia,
    linestyle=":",
    label="Inicio de anomalía (60 s)"
)

plt.axhline(
    umbral_caudal,
    linestyle="--",
    label="Umbral multisensor (96 mL/h)"
)

plt.xlabel("Tiempo (s)")
plt.ylabel("Caudal (mL/h)")

plt.title(
    "Figura 5.1. Comportamiento del caudal "
    "en los escenarios simulados"
)

plt.xlim(0, duracion)
plt.ylim(-5, 135)
plt.grid(True, alpha=0.3)
plt.legend(fontsize=8, ncol=2)
plt.tight_layout()

plt.savefig(
    carpeta / "figura_5_1_caudal.png",
    dpi=300
)

plt.show()


# ==============================================================
# 9. FIGURA 5.2: PRESIÓN
# ==============================================================

plt.figure(figsize=(11, 6))

for nombre, senales in escenarios.items():

    plt.plot(
        tiempo,
        senales["presion"],
        linewidth=2,
        label=nombre
    )

plt.axvline(
    inicio_anomalia,
    linestyle=":",
    label="Inicio de anomalía (60 s)"
)

plt.axhline(
    umbral_presion,
    linestyle="--",
    label="Umbral multisensor (50 mmHg)"
)

plt.axhline(
    umbral_convencional,
    linestyle="--",
    label="Umbral convencional (100 mmHg)"
)

plt.xlabel("Tiempo (s)")
plt.ylabel("Presión (mmHg)")

plt.title(
    "Figura 5.2. Variación de presión "
    "en la línea de infusión"
)

plt.xlim(0, duracion)
plt.ylim(0, 140)
plt.grid(True, alpha=0.3)
plt.legend(fontsize=8, ncol=2)
plt.tight_layout()

plt.savefig(
    carpeta / "figura_5_2_presion.png",
    dpi=300
)

plt.show()


# ==============================================================
# 10. FIGURA 5.3: CORRIENTE ELÉCTRICA
# ==============================================================

plt.figure(figsize=(11, 6))

for nombre, senales in escenarios.items():

    plt.plot(
        tiempo,
        senales["corriente"],
        linewidth=2,
        label=nombre
    )

plt.axvline(
    inicio_anomalia,
    linestyle=":",
    label="Inicio de anomalía (60 s)"
)

plt.axhline(
    umbral_corriente,
    linestyle="--",
    label="Umbral complementario (0.33 A)"
)

plt.xlabel("Tiempo (s)")
plt.ylabel("Corriente (A)")

plt.title(
    "Figura 5.3. Comportamiento de la corriente del motor"
)

plt.xlim(0, duracion)
plt.ylim(0.27, 0.36)
plt.grid(True, alpha=0.3)
plt.legend(fontsize=8, ncol=2)
plt.tight_layout()

plt.savefig(
    carpeta / "figura_5_3_corriente.png",
    dpi=300
)

plt.show()


# ==============================================================
# 11. FIGURA 5.4: COMPARACIÓN DE TIEMPOS DE DETECCIÓN
# ==============================================================

casos = [
    "Obstrucción parcial",
    "Obstrucción completa",
    "Falla del sensor óptico"
]

convencional = [
    resultados[n]["convencional"]
    for n in casos
]

multisensor = [
    resultados[n]["multisensor"]
    for n in casos
]

posiciones = np.arange(len(casos))
ancho = 0.35

plt.figure(figsize=(10, 6))

barras1 = plt.bar(
    posiciones - ancho / 2,
    [0 if v is None else v for v in convencional],
    ancho,
    label="Sistema convencional"
)

barras2 = plt.bar(
    posiciones + ancho / 2,
    [0 if v is None else v for v in multisensor],
    ancho,
    label="Sistema multisensor"
)

for barras, valores in [
    (barras1, convencional),
    (barras2, multisensor)
]:

    for barra, valor in zip(barras, valores):

        x_texto = (
            barra.get_x() + barra.get_width() / 2
        )

        if valor is None:

            plt.text(
                x_texto,
                0.25,
                "No detecta",
                ha="center",
                va="bottom",
                rotation=90,
                fontsize=8
            )

        else:

            plt.text(
                x_texto,
                valor + 0.15,
                f"{valor:.1f} s",
                ha="center",
                va="bottom",
                fontsize=9
            )

plt.xticks(
    posiciones,
    casos,
    rotation=10,
    ha="right"
)

plt.ylabel(
    "Tiempo desde la anomalía hasta la detección (s)"
)

plt.title(
    "Figura 5.4. Comparación de los tiempos de detección"
)

plt.ylim(0, 11)
plt.grid(axis="y", alpha=0.3)
plt.legend()
plt.tight_layout()

plt.savefig(
    carpeta / "figura_5_4_tiempos.png",
    dpi=300
)

plt.show()


# ==============================================================
# 12. MENSAJE FINAL
# ==============================================================

print("\n==============================================")
print("SIMULACIÓN FINALIZADA")
print("==============================================")

print("Se generaron correctamente:")
print("1. Figura de caudal.")
print("2. Figura de presión.")
print("3. Figura de corriente.")
print("4. Figura comparativa de tiempos.")
print("5. Tabla de resultados CSV.")
print("6. Datos completos de la simulación CSV.")
print("7. Resumen de resultados TXT.")

print("\nUbicación de los archivos:")
print(carpeta.resolve())

print("\nIMPORTANTE:")
print("Los resultados son hipotéticos y computacionales.")
print("No representan validación experimental ni clínica.")
