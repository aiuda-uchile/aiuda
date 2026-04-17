export default function TermsPt({ onClose }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-xl w-full
          max-w-lg md:max-w-2xl lg:max-w-3xl
          max-h-[80vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
        
        <h2 className="text-xl font-bold mb-4 px-10 pt-10">
          Termos de Uso 
        </h2>
        <h3 className="text-xl font-bold mb-2 px-10">Aiuda</h3>

        <div className="px-6 overflow-y-auto mx-auto wp-95">
          <p className="text-lg font-semibold mb-4">
            Plataforma de apoio à acessibilidade para docentes universitários
          </p>

          <p className="text-base">
            Ao baixar, instalar, acessar ou utilizar qualquer funcionalidade desta plataforma, você (doravante, "Usuário/a") declara ter lido, compreendido e aceitado integralmente todas as cláusulas aqui expostas.
          </p>

          <h3 className="text-lg font-semibold mt-4">
            Identificação
          </h3>

          <p className="text-md mb-2">
            <strong>Aiuda</strong> é um desenvolvimento criado no âmbito do <strong>Labs UniversitarIA</strong>, uma iniciativa de colaboração interuniversitária impulsionada pela Secretaria-Geral Ibero-Americana (SEGIB), organismo internacional de apoio aos 22 países que compõem a comunidade ibero-americana.
          </p>

          <p className="text-md mb-2">
            Este laboratório é impulsionado pela Divisão de Inovação Pública e Cidadã (DIPyC) da SEGIB em parceria com cinco universidades públicas ibero-americanas: Universidade da Corunha (UDC - Espanha), Universidade do Chile (UCHILE - Chile), Universidade Tecnológica do Uruguai (UTEC - Uruguai), Universidade de Buenos Aires (UBA - Argentina) e Universidade Federal do Rio de Janeiro (UFRJ - Brasil). O objetivo é desenvolver soluções de inteligência artificial centradas nas pessoas, com enfoque ético, inclusivo e contextualizado, para enfrentar desafios institucionais e sociais a partir das universidades públicas, promovendo soberania tecnológica e fortalecimento institucional.
          </p>

          <p className="text-md mb-2">
            <strong>Aiuda</strong> pretende ser uma solução que cada universidade possa instalar em sua própria infraestrutura, sem necessidade de serviços de terceiros, oferecendo apoio a docentes para legendagem, tradução e/ou análise de apresentações, com o objetivo de melhorar as condições de acessibilidade nos ambientes universitários.
          </p>

          <p className="text-md mb-2">
            A equipe de desenvolvimento foi formada, em ordem alfabética, por: José Joaquim de Moura Ramos (UDC), Bruna de Vargas Guterres (UTEC), José Antonio dos Santos Borges (UFRJ), Lia Fernanda Izquierdo (UBA), Dario Riquelme Zornow (UCHILE), Alicia Gabriela Rosenthal (UBA), Fernando Javier Valladares (UBA); e, em conjunto, acordaram estabelecer um licenciamento Creative Commons para esta solução.
          </p>

          <p className="text-md mb-2">
            O ponto de contato em relação a este documento é a Divisão de Inovação Pública e Cidadã (DIPyC) da SEGIB, cuja sede está localizada em:
          </p>

          <p className="text-md mb-2">
              Paseo de Recoletos, 8 <br />
              28001 Madrid, Espanha <br />
              Telefone: (+34) 915 901 980 <br />
              info@segib.org
          </p>

          <h3 className="text-lg font-semibold mt-6">
            Aceitação das Regras:
          </h3>

          <p className="text-md mb-2">
            O acesso à Plataforma ou a qualquer de seus componentes está estritamente condicionado à aceitação integral destes termos. Caso o/a Usuário/a não concorde com alguma das condições, deverá abster-se imediatamente de utilizar os serviços. O uso contínuo do sistema será interpretado como aceitação tácita, voluntária e definitiva de todas as regras vigentes.
          </p>

          <h4 className="text-base mb-2 mt-2">
            Natureza do serviço e “estado atual”
          </h4>

          <p className="text-md mb-2">
            A Plataforma é fornecida "como está" (as is) e "conforme disponibilidade" (as available). Tanto a SEGIB quanto a equipe de desenvolvimento não garantem que o serviço será ininterrupto, livre de erros, preciso ou totalmente seguro. O/a Usuário/a reconhece que o software é inerentemente suscetível a falhas técnicas e assume voluntariamente todos os riscos associados ao seu uso.
          </p>

          <h4 className="text-base mb-2 mt-2">
            Renúncia explícita a reclamações por danos
          </h4>

          <p className="text-md mb-2">
            Ao aceitar estes termos, o/a Usuário/a renuncia de forma irrevogável, total e absoluta a exercer qualquer direito de reclamação, demanda ou ação judicial posterior contra a SEGIB, a equipe de desenvolvimento, seus afiliados ou colaboradores, por:
          </p>

          <ul className="list text-md">
            <li>
              Danos diretos ou indiretos: incluindo perda de dados, lucros cessantes ou interrupção de negócios.
            </li>
            <li>
              Danos morais ou materiais: decorrentes de falhas no sistema, vulnerabilidades de segurança ou perda de informações.
            </li>
            <li>
              <p className="mb-4">Erros de terceiros: qualquer dano causado por serviços externos integrados à Plataforma.</p>
              <p>
                <strong>Nota Crítica:</strong> Em nenhuma circunstância o/a Desenvolvedor/a será responsável perante o/a Usuário/a por quaisquer danos ou prejuízos, mesmo que tenha sido previamente advertido da possibilidade de tais danos.
              </p>
            </li>
          </ul>

          <h3 className="text-lg font-semibold mt-4">
            Indenização
          </h3>

          <p className="text-md mb-2">
            O/a Usuário/a compromete-se a isentar a SEGIB, a equipe de desenvolvimento e seus colaboradores de qualquer reclamação de terceiros decorrente do uso da Plataforma ou do descumprimento destes termos.
          </p>

          <h3 className="text-lg font-semibold mt-4">
            Propriedade Intelectual
          </h3>

          <p className="text-md mb-2">
            A propriedade intelectual de <strong>Aiuda</strong> pertence aos sete membros da equipe de desenvolvimento, sendo uma obra colaborativa conforme descrito na seção “Identificação”.
          </p>

          <p className="text-md mb-2">
            O licenciamento adotado para <strong>Aiuda</strong> é Creative Commons, o que mantém a propriedade intelectual do produto original com os autores já identificados.
          </p>

          <h3 className="text-lg font-semibold mt-4">
            Uso Permitido e Proibido
          </h3>

          <p className="text-md mb-2">
            <strong>Aiuda</strong> foi inicialmente concebida como uma ferramenta voltada à acessibilidade para docentes universitários dos países membros da SEGIB. No entanto, por ser uma ferramenta gratuita e de código aberto, pode ser adotada por outras instituições educacionais e similares.
          </p>

          <p className="text-md mb-2">
            <strong>Aiuda</strong> utiliza licença Creative Commons e permite compartilhar e adaptar o código-fonte. “Compartilhar” permite copiar e redistribuir o material em qualquer meio ou formato. “Adaptar” permite modificar, transformar e criar novas soluções com base neste projeto.
          </p>

          <p className="text-md mb-2">
            Esses usos estão sujeitos às seguintes condições:
          </p>

          <p className="text-md mb-2">
            <strong>Atribuição (BY):</strong> Deve ser dado o devido crédito à equipe e à SEGIB, incluindo link da licença e indicação de alterações realizadas.
          </p>

          <p className="text-md mb-2">
            <strong>Uso não comercial (NC):</strong> Não é permitido uso comercial do material.
          </p>

          <p className="text-md mb-2">
            <strong>Compartilhar pela mesma licença (SA):</strong> Obras derivadas devem manter a mesma licença.
          </p>

          <p className="text-md mb-2">
            É estritamente proibido o uso desta aplicação para criar obras com malware ou mecanismos de coleta de dados sensíveis.
          </p>

          <p className="text-md mb-2">
            Também não é permitido distribuir ou armazenar conteúdo ilegal ou ofensivo.
          </p>

          <h3 className="text-lg font-semibold mt-4">
            Cláusula de uso aceitável
          </h3>

          <p className="text-md mb-2">
            Não é permitido utilizar a plataforma para promover conteúdos ilegais ou prejudiciais.
          </p>

          <h3 className="text-lg font-semibold mt-4">
            Mudanças no licenciamento
          </h3>

          <p className="text-md mb-2">
            A SEGIB reserva-se o direito de modificar os termos conforme evolução da ferramenta. O uso contínuo implica aceitação dos novos termos.
          </p>

          <img src="/aiuda/assets/by-nc-sa.png" alt="Licença Creative Commons" className="mt-2" width="150"/>

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
            Fechar
          </button>
        </div>
      </div>
    </div>
  )
}