export default function TermsGl({ onClose , getPublicAssetUrl }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-xl w-full
          max-w-lg md:max-w-2xl lg:max-w-3xl
          max-h-[80vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
        
        <h2 className="text-xl font-bold mb-4 px-10 pt-10">
          Condicións de uso
        </h2>
        <h3 className="text-xl font-bold mb-2 px-10">Aiuda</h3>
        <div className="px-6 overflow-y-auto mx-auto wp-95">
          <p className="text-lg font-semibold mb-4">
            Plataforma de apoio á accesibilidade para profesorado universitario
          </p>
          <p className="text-base">
            Ao descargar, instalar, acceder ou usar calquera funcionalidade desta plataforma, vostede (en diante, "o Usuario") declara que leu, comprendeu e aceptou todas as cláusulas aquí establecidas.
          </p>
          <h3 className="text-lg font-semibold mt-4">
            Identificación
          </h3>
          <p className="text-md mb-2">
            <strong>Aiuda</strong> es un desarrollo nacido en torno a <strong> Labs UniversitarIA,</strong> una iniciativa de colaboración interuniversitaria impulsada por la Secretaría General Iberoamericana (SEGIB), organismo internacional de apoyo a los 22 países que conforman la comunidad iberoamericana.
          </p>
          <p className="text-md mb-2">
            Este laboratorio está impulsado pola División de Innovación Pública e Cidadá (DIPyC) da SEGIB en colaboración con cinco universidades públicas iberoamericanas: a Universidade da Coruña (UDC - España), a Universidade de Chile (UCHILE - Chile), a Universidade Tecnolóxica do Uruguai (UTEC - Uruguai), a Universidade de Bos Aires (UBA - Arxentina) e a Universidade Federal do Río de Janeiro (UFRJ - Brasil). O obxectivo é desenvolver solucións de intelixencia artificial centradas no ser humano cun enfoque ético, inclusivo e contextualizado para abordar os desafíos institucionais e sociais desde as universidades públicas, promovendo a soberanía tecnolóxica e o fortalecemento institucional. 
          </p>
          <p className="text-md mb-2">
            <strong>Aiuda</strong> pretende ser unha solución que cada universidade poida instalar na súa infraestrutura sen precisar de servizos de terceiros; ofrecendo apoio ao profesorado para a subtitulación, tradución e/ou análise de presentacións, co fin de acadar mellores condicións de accesibilidade nos entornos universitarios.
          </p>
          <p className="text-md mb-2">
            O equipo de desenvolvemento estivo formado, alfabeticamente, por: José Joaquim de Moura Ramos (UDC), Bruna de Vargas Guterres (UTEC), José Antonio dos Santos Borges (UFRJ), Lia Fernanda Izquierdo (UBA), Dario Riquelme Zornow (UCHILE), Alicia Gabriela Rosenthal (UBA), Fernando Javier Valladares (UBA); e xuntos acordaron establecer unha licenza Creative Commons para esta solución.
          </p>
          <p className="text-md mb-2">
            O punto de contacto en relación con este documento é a División de Innovación Pública e Cidadá (DIPyC) da SEGIB, cuxa sede se atopa en: 
          </p>
          <p className="text-md mb-2">
              Paseo de Recoletos, 8 <br />
              28001 Madrid, España <br />
              Teléfono: (+34) 915 901 980 <br />
              info@segib.org
          </p>
          <h3 className="text-lg font-semibold mt-6">
            Aceptación das regras:
          </h3>
          <p className="text-md mb-2">
            O acceso á Plataforma ou a calquera dos seus compoñentes está estritamente condicionado á aceptación sen reservas destas condicións. Se o Usuario non está de acordo con algunha das condicións, deberá absterse inmediatamente de usar os servizos. O uso continuado do sistema interpretarase como unha aceptación tácita, voluntaria e definitiva de todas as normas aplicables.
          </p>
          <h4 className="text-base mb-2 mt-2">
            Natureza do servizo e "estado actual"
          </h4>
          <p className="text-md mb-2">
            A Plataforma ofrécese "tal cal" e "segundo dispoñibilidade". Nin SEGIB nin o equipo de desenvolvemento garanten que o servizo sexa ininterrompido, libre de erros, preciso ou completamente seguro. O Usuario recoñece que o software é inherentemente susceptible a fallos técnicos e asume voluntariamente todos os riscos asociados ao seu uso.
          </p>
          <h4 className="text-base mb-2 mt-2">
            Renuncia explícita ás reclamacións por danos e perdas
          </h4>
          <p className="text-md mb-2">
            Ao aceptar estas condicións, o Usuario renuncia de forma irrevocable, total e absoluta a calquera dereito de exercer calquera reclamación, demanda ou acción legal posterior contra SEGIB, o equipo de desenvolvemento, os seus afiliados ou colaboradores, polos seguintes motivos:</p>
          <ul className="list text-md">
            <li>
              Danos directos ou indirectos: incluíndo perda de datos, perda de beneficios ou interrupción da actividade empresarial.
            </li>
            <li>
              Danos morais ou materiais: derivados de fallos do sistema, vulnerabilidades de seguridade ou perda de información.
            </li>
            <li>
              <p className="mb-4">Erros de terceiros: Calquera dano causado por servizos externos integrados na Plataforma.</p>
              <p>
                <strong>Nota Crítica:</strong> En ningunha circunstancia o Desenvolvedor será responsable ante o Usuario por ningún dano ou perda, mesmo se foi previamente advertido da posibilidade de tales danos.
              </p>
            </li>
          </ul>
          <h3 className="text-lg font-semibold mt-4">
            Compensación
          </h3>
          <p className="text-md mb-2">
            O Usuario comprométese a indemnizar a SEGIB, o equipo de desenvolvemento ou os seus colaboradores fronte a calquera reclamación de terceiros derivada do uso da Plataforma por parte do Usuario ou do incumprimento destas condicións.
          </p>
          <h3 className="text-lg font-semibold mt-4">
            Propiedade Intelectual
          </h3>
          <p className="text-md mb-2">
            A propiedade intelectual de <strong>Aiuda</strong> é obra dos sete membros do equipo de desenvolvemento, é dicir, é un traballo colaborativo do equipo individualizado na sección "Identificación".
          </p>
          <p className="text-md mb-2">
            O réxime de licenzas escollido para <strong>Aiuda</strong> é Creative Commons, o que fai que a propiedade intelectual do produto inicial persista nas persoas xa identificadas.
          </p>
          <h3 className="text-lg font-semibold mt-4">
          Usos permitidos e prohibidos
          </h3>
          <p className="text-md mb-2">
            <strong>Aiuda</strong> inicialmente foi deseñado como unha ferramenta para mellorar a accesibilidade do profesorado nas universidades dos países pertencentes á SEGIB. Non obstante, entendemos que, ao ser unha ferramenta gratuíta e de código aberto, pode ser adoptada por calquera institución educativa e organizacións similares.
          </p>
          <p className="text-md mb-2">
            <strong>Aiuda</strong> emprega unha licenza Creative Commons e concede permisos para compartir e adaptar o código fonte. "Compartir" permite copiar e redistribuír o material en calquera medio ou formato. "Adaptar" permite reorganizar, transformar, modificar e crear novas solucións baseadas neste proxecto.
          </p>
          <p className="text-md mb-2">
            Estes usos permitidos están suxeitos ás seguintes restricións:
          </p>
          <p className="text-md mb-2">
            <strong>Requírese atribución (BY)</strong>: debes darlle o crédito axeitado ao equipo de desenvolvemento e a SEGIB, proporcionar unha ligazón á licenza e indicar se se realizaron cambios. Podes facelo de calquera xeito razoable, pero non de ningún xeito que suxira que o licenciante te avala a ti ou ao teu uso.
          </p>
          <p className="text-md mb-2">
            <strong>Uso non comercial (NC):</strong> Non podes usar o material con fins comerciais, nin o orixinal nin as obras derivadas.
          </p>
          <p className="text-md mb-2">
            <strong>Compartir igual (SA):</strong> Se remesturas, transformas ou creas obras derivadas do material, debes distribuír as túas contribucións coa mesma licenza que o orixinal.
          </p>
          <p className="text-md mb-2">
            O uso desta aplicación para crear obras derivadas que conteñan software malicioso ou mecanismos que permitan a recollida de información persoal confidencial, incluíndo nomes, enderezos de correo electrónico e os obxectos virtuais utilizados (presentacións, audio, vídeo, etc.), está estritamente prohibido. </p>
          <p className="text-md mb-2">
            Non se pode usar para distribuír ou almacenar contido ofensivo, ilegal ou que poña en risco a infraestrutura e as persoas, xa sexa dentro das organizacións onde se usa ou para os seus usuarios, estean onde estean.
          </p>
          <h3 className="text-lg font-semibold mt-4">
            Cláusula de uso aceptable
          </h3>
          <p className="text-md mb-2">
            A plataforma non se pode empregar para crear, almacenar, distribuír ou promover contido ilegal, ofensivo ou potencialmente perigoso que poida poñer en perigo a seguridade das persoas, os sistemas ou a infraestrutura.
          </p>
          <p className="text-md mb-2">
            Isto inclúe, entre outros, materiais que:
          </p>
          <ul className="list text-md">
            <li>
              promover, incitar ou lexitimar o odio, a violencia ou a discriminación contra persoas ou grupos baseándose en atributos como a orixe, nacionalidade, etnia, xénero, identidade de xénero, orientación sexual, relixión, idade, discapacidade ou outras condicións persoais ou sociais;
            </li>
            <li>
              conter ameazas, acoso, intimidación ou calquera forma de violencia simbólica ou física;
            </li>
            <li>
              promover actividades ilícitas ou condutas que violen os dereitos humanos fundamentais;
            </li>
            <li>
              implicar a difusión de contidos que poidan causar danos físicos, psicolóxicos, sociais ou de reputación a individuos, comunidades ou organizacións.
            </li>
          </ul>
          <p className="text-md mb-2">
            Estas restricións aplícanse independentemente do formato, medio ou localización xeográfica dos usuarios.
          </p>
          <p className="text-md mb-2">
            La interpretación de estas disposiciones se realizará conforme a la normativa vigente y a principios de respeto, inclusión y no discriminación.
          </p>
          <h3 className="text-lg font-semibold mt-4">
            Cambios nas licenzas
          </h3>
          <p className="text-md mb-2">
            A SEGIB resérvase o dereito de modificar os termos da licenza de acordo coa evolución técnica e xurídica da ferramenta. O uso continuado da aplicación despois de tales cambios implica a aceptación dos novos termos. Para a resolución de disputas, as partes acordan expresamente someterse ás leis e tribunais da cidade onde a universidade implementadora establece o seu domicilio social, renunciando irrevocablemente ao seu propio foro ou domicilio.
          </p>
          <img src={getPublicAssetUrl("assets/by-nc-sa.png")} alt="Licenza Creative Commons" className="logo-footer2"/>
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
            Pechar
          </button>
        </div>
      </div>
    </div>
  )
}