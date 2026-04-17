export default function TermsPt({ onClose }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-xl w-full
          max-w-lg md:max-w-2xl lg:max-w-3xl
          max-h-[80vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
        
        <h2 className="text-xl font-bold mb-4 px-10 pt-10">
          Términos de Uso Aiuda Pt
        </h2>
        <div className="px-6 overflow-y-auto mx-auto wp-95">
          <p className="text-lg font-semibold mb-4">
            Plataforma de apoyo a la inclusión para docentes universitarios
          </p>
          <p className="text-base">
            Al descargar, instalar, acceder o utilizar cualquier funcionalidad de esta plataforma, usted (en adelante, "el Usuario") declara haber leído, comprendido y aceptado la totalidad de las cláusulas aquí expuestas.
          </p>
          <h3 className="text-lg font-semibold mt-4">
            Identificación
          </h3>
          <p className="text-md mb-2">
            ”aiuda” es un desarrollo nacido en torno a “labs universitarIA” organizados por SEGIB, Secretaría General Iberoamericana, organismo que organismo internacional de apoyo a los 22 países que conforman la comunidad iberoamericana.
          </p>
          <p className="text-md mb-2">
            Este laboratorio es Impulsado por la División de Innovación Pública y Ciudadana (DIPyC) de la SEGIB en alianza con cinco universidades públicas iberoamericanas: UBA, UFRJ, UChile, UDC y UTEC; de Argentina, Brasil, Chile, Coruña y Uruguay respectivamente. Persiguió el desarrollar soluciones de inteligencia artificial centradas en las personas con enfoque ético, inclusivo y contextualizado para enfrentar desafíos institucionales y sociales desde las universidades públicas, promoviendo soberanía tecnológica y fortalecimiento institucional. 
          </p>
          <p className="text-md mb-2">
            Este proyecto pretende ser una solución que cada universidad pueda instalar en su infraestructura, sin requerir servicios de terceros, entregando una “ayuda” a docentes, para el subtitulado, traducción y análisis de presentaciones, con miras a conseguir mejores condiciones de accesibilidad e inclusión en los entornos universitarios.
          </p>
          <p className="text-md mb-2">
            El equipo de desarrollo estuvo formado, alfabéticamente,  por :
              José Joaquim de Moura Ramos (UDC), Bruna de Vargas Guterres (UTEC), José Antonio dos Santos Borges (UFRJ), Lia Fernanda Izquierdo (UBA), Dario Riquelme Zornow (UCHILE), Alicia Gabriela Rosenthal (UBA), Fernando Javier Valladares (UBA); y en conjunto han acordado establecer un licenciamiento Creative Commons para esta solución.
          </p>
          <p className="text-md mb-2">
            El punto de contacto respecto a este documento, es la División de Innovación Pública y Ciudadana (DIPyC) de la SEGIB, cuya sede está situada en: 
          </p>
          <p className="text-md mb-2">
              Paseo de Recoletos, 8 <br />
              28001 Madrid, España <br />
              Teléfono: (+34) 915 901 980 <br />
              info@segib.org
          </p>
          <h3 className="text-lg font-semibold mt-6">
            Aceptación de las Reglas:
          </h3>
          <p className="text-md mb-2">
            El acceso a la Plataforma o cualquiera de sus componentes, está estrictamente condicionado a la aceptación sin reservas de estos términos. <strong> Si el Usuario no está de acuerdo con alguna de las condiciones, deberá abstenerse inmediatamente de utilizar los servicios.</strong> El uso continuo del sistema se interpretará como una aceptación tácita, voluntaria y definitiva de todas las reglas vigentes.
          </p>
          <h4 className="text-base mb-2 mt-2">
            NATURALEZA DEL SERVICIO Y "ESTADO ACTUAL"
          </h4>
          <p className="text-md mb-2">
            La Plataforma se entrega "tal cual" <strong>(AS IS) </strong> y "según disponibilidad" <strong>(AS AVAILABLE)</strong>. El SEGIB y el equipo de desarrollo, no garantiza que el servicio sea ininterrumpido, libre de errores, exacto o completamente seguro. El Usuario reconoce que el software es inherentemente susceptible a fallos técnicos y asume voluntariamente todos los riesgos asociados a su uso.
          </p>
          <h4 className="text-base mb-2 mt-2">
            RENUNCIA EXPLÍCITA A RECLAMACIONES POR DAÑOS
          </h4>
          <p className="text-md mb-2">
            Al aceptar estos términos, el Usuario renuncia de manera irrevocable, total y absoluta a ejercer cualquier derecho de reclamo, demanda o acción legal posterior contra el SEGIB, el equipo de desarrollo, sus afiliados o colaboradores, por concepto de:
          </p>
          <ul className="list text-md">
            <li>
              <strong> Daños directos o indirectos: </strong> Incluyendo pérdida de datos, lucro cesante o interrupción de negocios.
            </li>
            <li>
              <strong>Perjuicios morales o materiales:</strong> Derivados de fallos en el sistema, vulnerabilidades de seguridad o pérdida de información.
            </li>
            <li>
              <p className="mb-4"><strong>Errores de terceros:</strong> Cualquier daño causado por servicios externos integrados en la Plataforma.</p>
              <p>
                <strong>Nota Crítica:</strong> Bajo ninguna circunstancia el Desarrollador será responsable ante el Usuario por cualquier daño o perjuicio, incluso si se hubiera advertido previamente de la posibilidad de tales daños.
              </p>
            </li>
          </ul>
          
        </div>
        <div className="flex justify-end p-6">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-color-primary text-white"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  )
}