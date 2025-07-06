from utilidades import get_google_drive_service
import traceback

if __name__ == "__main__":
    print("🚀 Iniciando proceso de generación de token de Google Drive...")
    print("Este script te guiará para autorizar el acceso a Google Drive.")
    print("Asegúrate de que 'client_secret.json' está en tu carpeta './config'.")
    print("Si ya existe un 'token.json' válido, este script intentará refrescarlo o te indicará que es válido.")
    print("----------------------------------------------------------------------")
    
    try:
        # Llamar a la función que contiene la lógica de autenticación y el input()
        get_google_drive_service()
        print("----------------------------------------------------------------------")
        print("✅ Token generado/refrescado y guardado exitosamente en config/token.json.")
        print("   Este archivo ahora está en tu carpeta local './config' debido al montaje de volumen.")
        print("Ahora puedes iniciar la aplicación principal con: docker-compose up")
    except EOFError:
        print("----------------------------------------------------------------------")
        print("❌ ERROR: Se esperaba una entrada (el código de autorización), pero no se recibió.")
        print("   Asegúrate de que estás ejecutando este script en un terminal interactivo.")
        print("   Si copiaste la URL y obtuviste un código, intenta pegarlo y presionar Enter rápidamente.")
        print(f"   Detalles del error: {traceback.format_exc()}")
    except Exception as e:
        print("----------------------------------------------------------------------")
        print(f"❌ Error durante la generación del token: {str(e)}")
        print(f"   Detalles del error: {traceback.format_exc()}")
        print("   Por favor, verifica tu 'client_secret.json', la conexión a internet,")
        print("   y asegúrate de seguir correctamente los pasos de autorización en el navegador.") 