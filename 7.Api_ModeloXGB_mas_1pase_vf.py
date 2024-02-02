import streamlit as st
import numpy as np
import joblib

# Variables Constantes
##En porcentaje, se define cual es el factor de llenado en peso, que es manejado mas por el expertise del Operador (Por el momento se mantiene asi)
factor_llenado_peso = 0.9

#En porcentaje, se define cual es el factor de llenado en peso, que es manejado mas por el expertise del Operador (Por el momento se mantiene asi)
factor_llenado_volumen = 0.9 

# Variable que se completo de acuerdo al expertise, pero puedo cambiar en las operaciones
payload = 1.05     # Sera constante por el momento

# Variable que se completo de acuerdo al expertise, pero puedo cambiar en las operaciones
capacidad_llenado_vol = 1.05 


# Cargar el modelo y su scaler para normalización
model_xgb = joblib.load('modelo_xgb_6var.pkl')
# scaler = joblib.load('scaler_modelo_xgb_6var_N.pkl')

def realizar_prediccion(model, input_features):
    # Realizar la predicción utilizando el modelo cargado
    prediction = model.predict(input_features)
    rounded_prediction = np.round(prediction).astype('int64')
    return rounded_prediction

def calcular_operacion_matematica(capacidad_en_peso_equipo_carguio, capacidad_en_volumen_equipo_carguio_m3,
                                 capacidad_en_peso_equipo_acarreo, densidad_inicial_poligono_creado_tn_m3,
                                 tiene_camion_cuadrado, tonelaje_acumulado_anterior_carga, tonelaje_acumulado_carga,
                                 capacidad_en_volumen_equipo_acarreo_m3):

    # Verificar si el denominador es diferente de cero
    if densidad_inicial_poligono_creado_tn_m3 != 0:
        if ((capacidad_en_peso_equipo_carguio * factor_llenado_peso) / densidad_inicial_poligono_creado_tn_m3) > \
                (capacidad_en_volumen_equipo_carguio_m3 * factor_llenado_volumen):
            cargado_real_cuchara_ton = capacidad_en_volumen_equipo_carguio_m3 * densidad_inicial_poligono_creado_tn_m3 * factor_llenado_volumen
        else:
            cargado_real_cuchara_ton = capacidad_en_peso_equipo_carguio * factor_llenado_peso
    else:
        # Si el denominador es cero, establecer cargado_real_cuchara_ton en cero
        cargado_real_cuchara_ton = 0


    # Verificar si cargado_real_cuchara_ton es diferente de cero antes de realizar la división
    pases_depositados = tonelaje_acumulado_carga / cargado_real_cuchara_ton if cargado_real_cuchara_ton != 0 else 0


    if capacidad_en_volumen_equipo_carguio_m3 == 0:
        calculo_promedio_densidad_ton_m3 = densidad_inicial_poligono_creado_tn_m3
    else:
        calculo_promedio_densidad_ton_m3 = 0 if cargado_real_cuchara_ton == 0 else \
                                   (densidad_inicial_poligono_creado_tn_m3 * \
                                   (tonelaje_acumulado_carga - tonelaje_acumulado_anterior_carga)) / \
                                   cargado_real_cuchara_ton

    # Verificar si pases_depositados es diferente de cero
    denominador_pases = capacidad_en_volumen_equipo_carguio_m3 * pases_depositados
    if denominador_pases != 0:
        # Calcular densidad_material_pase_ton_m3
        densidad_material_pase_ton_m3 = np.mean([densidad_inicial_poligono_creado_tn_m3, calculo_promedio_densidad_ton_m3,
                                                tonelaje_acumulado_carga / denominador_pases])
    else:
        densidad_material_pase_ton_m3 = 0


    # Verificar si densidad_material_pase_ton_m3 es diferente de cero
    if densidad_material_pase_ton_m3 != 0:
        if ((capacidad_en_peso_equipo_acarreo * payload) / densidad_material_pase_ton_m3 > \
                capacidad_en_volumen_equipo_acarreo_m3 * capacidad_llenado_vol):
            tonelaje_requerido_camion_ton = capacidad_en_volumen_equipo_acarreo_m3 * densidad_material_pase_ton_m3 * capacidad_llenado_vol
        else:
            tonelaje_requerido_camion_ton = capacidad_en_peso_equipo_acarreo * payload
    else:
        # Si densidad_material_pase_ton_m3 es cero, establecer tonelaje_requerido_camion_ton en 0
        tonelaje_requerido_camion_ton = 0

    # Verificar si cargado_real_cuchara_ton es diferente de cero
    numero_cucharadas_requeridos = round(tonelaje_requerido_camion_ton / cargado_real_cuchara_ton, 2) if cargado_real_cuchara_ton != 0 else 0

    diferencia = numero_cucharadas_requeridos - pases_depositados

    if tiene_camion_cuadrado is True:
        if diferencia > 0.8:
            necesita_un_pase_mas = True
        else:
            necesita_un_pase_mas = False
    else:
        if diferencia > 0.2:
            necesita_un_pase_mas = True
        else:
            necesita_un_pase_mas = False

    return necesita_un_pase_mas


def main():
    st.title("Predicciones en tiempo real con XGBoost")

    # Inicializar el estado de la sesión
    if 'estado' not in st.session_state:
        st.session_state.estado = {
            'rounded_prediction': None,
            'tonelaje_acumulado_anterior_carga': None,
            'tonelaje_acumulado_carga': None,
            'necesita_un_pase_mas': None
        }

    capacidad_en_volumen_equipo_carguio_m3 = st.number_input('Capacidad en volumen del equipo de carguío (m3)', value=0.0, step=0.1)
    capacidad_en_peso_equipo_carguio = st.number_input('Capacidad en peso del equipo de carguío (ton)', value=0.0, step=0.1)
    capacidad_en_peso_equipo_acarreo = st.number_input('Capacidad en peso del equipo de acarreo (ton)', value=0.0, step=0.1)
    tonelaje_camion_antes_cargaestabilizada = st.number_input('Tonelaje del camión antes de la carga estabilizada (ton)', value=0.0, step=0.1)
    angulo_giro_promedio_pases = st.number_input('Ángulo de giro promedio en pases', value=0.0, step=0.1)
    densidad_inicial_poligono_creado_tn_m3 = st.number_input('Densidad inicial del polígono creado (ton/m3)', value=0.0, step=0.1)

    capacidad_en_volumen_equipo_acarreo_m3 = st.number_input('capacidad_en_volumen_equipo_acarreo_m3', value=0.0, step=0.1)
    tiene_camion_cuadrado = st.checkbox('¿Tiene camión cuadrado?')

    if st.button('Realizar Predicción y Algoritmo Matemático'):
        input_features = np.array([[capacidad_en_volumen_equipo_carguio_m3, capacidad_en_peso_equipo_carguio,
                                    capacidad_en_peso_equipo_acarreo, tonelaje_camion_antes_cargaestabilizada,
                                    angulo_giro_promedio_pases, densidad_inicial_poligono_creado_tn_m3]])

        rounded_prediction = realizar_prediccion(model_xgb, input_features)
        tonelaje_acumulado_anterior_carga = float(capacidad_en_peso_equipo_carguio * (rounded_prediction - 1))
        tonelaje_acumulado_carga = float(capacidad_en_peso_equipo_carguio * rounded_prediction)
        necesita_un_pase_mas = calcular_operacion_matematica(
            capacidad_en_peso_equipo_carguio, capacidad_en_volumen_equipo_carguio_m3, capacidad_en_peso_equipo_acarreo,
            densidad_inicial_poligono_creado_tn_m3, tiene_camion_cuadrado, tonelaje_acumulado_anterior_carga, tonelaje_acumulado_carga,
            capacidad_en_volumen_equipo_acarreo_m3)

        st.session_state.estado['rounded_prediction'] = rounded_prediction
        st.session_state.estado['tonelaje_acumulado_anterior_carga'] = tonelaje_acumulado_anterior_carga
        st.session_state.estado['tonelaje_acumulado_carga'] = tonelaje_acumulado_carga
        st.session_state.estado['necesita_un_pase_mas'] = necesita_un_pase_mas

        st.write(f'Predicción: {rounded_prediction}')
        st.write(f'¿Necesita un pase más?: {necesita_un_pase_mas}')

    if st.button('Agregar 1 pase más'):
        if st.session_state.estado['rounded_prediction'] is not None:
            st.session_state.estado['rounded_prediction'] += 1
            tonelaje_acumulado_anterior_carga = float(capacidad_en_peso_equipo_carguio * (st.session_state.estado['rounded_prediction'] - 1))
            tonelaje_acumulado_carga = float(capacidad_en_peso_equipo_carguio * st.session_state.estado['rounded_prediction'])
            necesita_un_pase_mas = calcular_operacion_matematica(
                capacidad_en_peso_equipo_carguio, capacidad_en_volumen_equipo_carguio_m3, capacidad_en_peso_equipo_acarreo,
                densidad_inicial_poligono_creado_tn_m3, tiene_camion_cuadrado, tonelaje_acumulado_anterior_carga, tonelaje_acumulado_carga,
                capacidad_en_volumen_equipo_acarreo_m3)

            st.session_state.estado['tonelaje_acumulado_anterior_carga'] = tonelaje_acumulado_anterior_carga
            st.session_state.estado['tonelaje_acumulado_carga'] = tonelaje_acumulado_carga
            st.session_state.estado['necesita_un_pase_mas'] = necesita_un_pase_mas

            st.write(f'Total Pases con 1 pase más: {st.session_state.estado["rounded_prediction"]}')
            st.write(f'¿Necesita un pase más?: {necesita_un_pase_mas}')

if __name__ == "__main__":
    main()
