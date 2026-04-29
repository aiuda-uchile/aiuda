export default function Terms({ onClose, getPublicAssetUrl }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-xl w-full
          max-w-lg md:max-w-2xl lg:max-w-3xl
          max-h-[80vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
        
        <h2 className="text-xl font-bold mb-4 px-10 pt-10">
          Términos de Uso 
        </h2>
        <h3 className="text-xl font-bold mb-2 px-10">Aiuda</h3>
        <div className="px-6 overflow-y-auto mx-auto wp-95">
          <p className="text-lg font-semibold mb-4">
            Plataforma de apoyo a la accesibilidad para docentes universitarios
          </p>
          <p className="text-base">
            Al descargar, instalar, acceder o utilizar cualquier funcionalidad de esta plataforma, usted (en adelante, "el/la Usuario/a") declara haber leído, comprendido y aceptado la totalidad de las cláusulas aquí expuestas.
          </p>
          <h3 className="text-lg font-semibold mt-4">
            Identificación
          </h3>
          <p className="text-md mb-2">
            <strong>Aiuda</strong> es un desarrollo nacido en torno a <strong> Labs UniversitarIA,</strong> una iniciativa de colaboración interuniversitaria impulsada por la Secretaría General Iberoamericana (SEGIB), organismo internacional de apoyo a los 22 países que conforman la comunidad iberoamericana.
          </p>
          <p className="text-md mb-2">
            Este laboratorio es impulsado por la División de Innovación Pública y Ciudadana (DIPyC) de la SEGIB en alianza con cinco universidades públicas iberoamericanas: Universidad de A Coruña (UDC - España), Universidad de Chile (UCHILE - Chile), Universidad Tecnológica del Uruguay (UTEC -Uruguay), Universidad de Buenos Aires (UBA - Argentina) y la Universidade Federal do Rio de Janeiro (UFRJ - Brasil). El objetivo es desarrollar soluciones de inteligencia artificial centradas en las personas con enfoque ético, inclusivo y contextualizado para enfrentar desafíos institucionales y sociales desde las universidades públicas, promoviendo soberanía tecnológica y fortalecimiento institucional. 
          </p>
          <p className="text-md mb-2">
            <strong>Aiuda</strong> pretende ser una solución que cada universidad pueda instalar en su infraestructura sin requerir servicios de terceros; ofreciendo apoyo a docentes para el subtitulado, la traducción y/o el análisis de presentaciones, con miras a conseguir mejores condiciones de accesibilidad en los entornos universitarios.
          </p>
          <p className="text-md mb-2">
            El equipo de desarrollo estuvo formado, alfabéticamente, por: José Joaquim de Moura Ramos (UDC), Bruna de Vargas Guterres (UTEC), José Antonio dos Santos Borges (UFRJ), Lia Fernanda Izquierdo (UBA), Dario Riquelme Zornow (UCHILE), Alicia Gabriela Rosenthal (UBA), Fernando Javier Valladares (UBA); y en conjunto han acordado establecer un licenciamiento Creative Commons para esta solución.
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
            El acceso a la Plataforma o cualquiera de sus componentes, está estrictamente condicionado a la aceptación sin reservas de estos términos. Si el/la Usuario/a no está de acuerdo con alguna de las condiciones, deberá abstenerse inmediatamente de utilizar los servicios. El uso continuo del sistema se interpretará como una aceptación tácita, voluntaria y definitiva de todas las reglas vigentes.
          </p>
          <h4 className="text-base mb-2 mt-2">
            Naturaleza del servicio y “estado actual”
          </h4>
          <p className="text-md mb-2">
            La Plataforma se entrega "tal cual" (as is) y "según disponibilidad" (as available). Tanto la SEGIB como el equipo de desarrollo no garantizan que el servicio sea ininterrumpido, libre de errores, exacto o completamente seguro. El/la Usuario/a reconoce que el software es inherentemente susceptible a fallos técnicos y asume voluntariamente todos los riesgos asociados a su uso.
          </p>
          <h4 className="text-base mb-2 mt-2">
            Renuncia explícita a reclamaciones por daños 
          </h4>
          <p className="text-md mb-2">
            Al aceptar estos términos, el/la Usuario/a renuncia de manera irrevocable, total y absoluta a ejercer cualquier derecho de reclamo, demanda o acción legal posterior contra la SEGIB, el equipo de desarrollo, sus afiliados o colaboradores, por concepto de:</p>
          <ul className="list text-md">
            <li>
              Daños directos o indirectos: Incluyendo pérdida de datos, lucro cesante o interrupción de negocios.
            </li>
            <li>
              Perjuicios morales o materiales: Derivados de fallos en el sistema, vulnerabilidades de seguridad o pérdida de información.
            </li>
            <li>
              <p className="mb-4">Errores de terceros: Cualquier daño causado por servicios externos integrados en la Plataforma.</p>
              <p>
                <strong>Nota Crítica:</strong> Bajo ninguna circunstancia el/la Desarrollador/a será responsable ante el/la Usuario/a por cualquier daño o perjuicio, incluso si se hubiera advertido previamente de la posibilidad de tales daños.
              </p>
            </li>
          </ul>
          <h3 className="text-lg font-semibold mt-4">
            Indemnización
          </h3>
          <p className="text-md mb-2">
            El/la Usuario/a se compromete a mantener indemne a SEGIB, equipo desarrollador o sus colaboradores, frente a cualquier reclamación de terceros derivada del uso que el/la Usuario/a haga de la Plataforma o del incumplimiento de estas condiciones.
          </p>
          <h3 className="text-lg font-semibold mt-4">
            Propiedad Intelectual
          </h3>
          <p className="text-md mb-2">
            La propiedad intelectual de <strong>Aiuda</strong> es de los siete miembros del equipo de desarrollo, es decir es una obra en colaboración del equipo individualizado en el acápite “Identificación”.
          </p>
          <p className="text-md mb-2">
            El esquema de licenciamiento escogido para <strong>Aiuda</strong> es Creative Commons, lo que hace persistir la propiedad intelectual de producto inicial en las personas ya identificadas.
          </p>
          <h3 className="text-lg font-semibold mt-4">
            Uso Permitido y Prohibido
          </h3>
          <p className="text-md mb-2">
            <strong>Aiuda</strong> fue diseñada, inicialmente, como una herramienta dedicada a ofrecer mejoras de accesibilidad a docentes de universidades de los países que forman parte de la SEGIB. Sin embargo, entendemos que siendo una herramienta de código abierto y gratuita, puede ser adoptada por todo establecimiento de educación y otros similares.
          </p>
          <p className="text-md mb-2">
            <strong>Aiuda</strong> utiliza la licencia Creative Commons y entrega autorizaciones para compartir y adaptar el código fuente. “Compartir” (share), permite copiar y redistribuir el material en cualquier medio o formato. “Modificar” (adapt), permite reorganizar, transformar, modificar y construir nuevas soluciones, con base a este proyecto.
          </p>
          <p className="text-md mb-2">
            Estos usos permitidos poseen las siguientes restricciones:.
          </p>
          <p className="text-md mb-2">
            <strong>Debe dar atribución (BY):</strong>Debe dar el crédito correspondiente al equipo de desarrollo y a SEGIB, proporcionar un enlace a la licencia e indicar si se realizaron cambios. Puede hacerlo de cualquier manera razonable, pero no de forma que sugiera que el licenciante lo respalda a usted o su uso.
          </p>
          <p className="text-md mb-2">
            <strong>Uso no comercial (NC):</strong> No se puede utilizar el material con fines comerciales, ni el original ni las obras derivadas.
          </p>
          <p className="text-md mb-2">
            <strong>Compartir en iguales condiciones (SA): </strong> Si remezcla, transforma o crea obras derivadas del material, debe distribuir sus contribuciones bajo la misma licencia que el original.
          </p>
          <p className="text-md mb-2">
            Queda estrictamente prohibido el uso de esta aplicación para realizar obras derivadas que contengan malware o mecanismos que permitan la recolección de información confidencial de las personas, incluyendo nombres, correos electrónicos y los objetos virtuales usados (presentaciones, audios, videos, etc.). 
          </p>
          <p className="text-md mb-2">
            No se puede usar para distribuir o almacenar contenido ofensivo, ilegal o que ponga en riesgo infraestructura y personas, en las organizaciones donde se utilice y en sus usuarios/as, donde sea que estén.
          </p>
          <h3 className="text-lg font-semibold mt-4">
            Cláusula de uso aceptable
          </h3>
          <p className="text-md mb-2">
            No se permite el uso de la plataforma para crear, almacenar, distribuir o promover contenidos ilegales, ofensivos o que puedan poner en riesgo la seguridad de las personas, los sistemas o la infraestructura.
          </p>
          <p className="text-md mb-2">
            Esto incluye, sin limitarse a, materiales que:
          </p>
          <ul className="list text-md">
            <li>
              promuevan, inciten o legitimen el odio, la violencia o la discriminación contra personas o grupos en función de atributos como origen, nacionalidad, etnia, género, identidad de género, orientación sexual, religión, edad, discapacidad u otras condiciones personales o sociales;
            </li>
            <li>
              contengan amenazas, acoso, hostigamiento o cualquier forma de violencia simbólica o física;
            </li>
            <li>
              fomenten actividades ilícitas o conductas que vulneren derechos humanos fundamentales;
            </li>
            <li>
              impliquen la difusión de contenido que pueda generar daño físico, psicológico, social o reputacional a individuos, comunidades u organizaciones.
            </li>
          </ul>
          <p className="text-md mb-2">
            Estas restricciones aplican independientemente del formato, medio o ubicación geográfica de los usuarios/as.
          </p>
          <p className="text-md mb-2">
            La interpretación de estas disposiciones se realizará conforme a la normativa vigente y a principios de respeto, inclusión y no discriminación.
          </p>
          <h3 className="text-lg font-semibold mt-4">
            Cambios en el licenciamiento
          </h3>
          <p className="text-md mb-2">
            SEGIB se reserva el derecho de modificar las condiciones de licenciamiento conforme a la evolución técnica y jurídica de la herramienta. El uso continuado de la aplicación tras dichos cambios implica la aceptación de los nuevos términos. Para la resolución de conflictos, las partes acuerdan la sumisión expresa a la legislación y tribunales de la ciudad donde la Universidad que ha implementado defina su domicilio, renunciando irrevocablemente a su propio fuero o domicilio.
          </p>
          <img src={getPublicAssetUrl("assets/by-nc-sa.png")} alt="Licencia Creative Commons" className="logo-footer2"/>
          <p className="text-md mt-4 mb-2">
            Elaborado por Darío Riquelme Z. <br />
            Revisado por Ana Abac
          </p>
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