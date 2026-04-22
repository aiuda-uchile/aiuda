export default function TermsEn({ onClose, getPublicAssetUrl }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-xl w-full
          max-w-lg md:max-w-2xl lg:max-w-3xl
          max-h-[80vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
        
        <h2 className="text-xl font-bold mb-4 px-10 pt-10">
          Terms of Use 
        </h2>
        <h3 className="text-xl font-bold mb-2 px-10">Aiuda</h3>
        <div className="px-6 overflow-y-auto mx-auto wp-95">
          <p className="text-lg font-semibold mb-4">   
            Accessibility support platform for university teachers
          </p>
          <p className="text-base">
            By downloading, installing, accessing or using any functionality of this platform, you (hereinafter, "the User") declare that you have read, understood and accepted all of the clauses set forth herein.
          </p>
          <h3 className="text-lg font-semibold mt-4">
            Identification
          </h3>
          <p className="text-md mb-2">
            <strong>Aiuda</strong> it is a development born around <strong> Labs UniversitarIA,</strong> an inter-university collaboration initiative promoted by the Ibero-American General Secretariat (SEGIB), an international organization that supports the 22 countries that make up the Ibero-American community.
          </p>
          <p className="text-md mb-2">
            This laboratory is driven by the Public and Citizen Innovation Division (DIPyC) of SEGIB in partnership with five Ibero-American public universities: the University of A Coruña (UDC - Spain), the University of Chile (UCHILE - Chile), the Technological University of Uruguay (UTEC - Uruguay), the University of Buenos Aires (UBA - Argentina), and the Federal University of Rio de Janeiro (UFRJ - Brazil). The objective is to develop human-centered artificial intelligence solutions with an ethical, inclusive, and contextualized approach to address institutional and social challenges from within public universities, promoting technological sovereignty and institutional strengthening.
          </p>
          <p className="text-md mb-2">
            <strong>Aiuda</strong> it aims to be a solution that each university can install in its infrastructure without requiring third-party services; offering support to teachers for subtitling, translation and/or analysis of presentations, with a view to achieving better accessibility conditions in university environments.
          </p>
          <p className="text-md mb-2">
            The development team consisted, alphabetically, of: José Joaquim de Moura Ramos (UDC), Bruna de Vargas Guterres (UTEC), José Antonio dos Santos Borges (UFRJ), Lia Fernanda Izquierdo (UBA), Dario Riquelme Zornow (UCHILE), Alicia Gabriela Rosenthal (UBA), Fernando Javier Valladares (UBA); and together they have agreed to establish a Creative Commons license for this solution.
          </p>
          <p className="text-md mb-2">
            
The point of contact regarding this document is the Public and Citizen Innovation Division (DIPyC) of the SEGIB, whose headquarters are located at:
          </p>
          <p className="text-md mb-2">
              Paseo de Recoletos, 8 <br />
              28001 Madrid, España <br />
              Teléfono: (+34) 915 901 980 <br />
              info@segib.org
          </p>
          <h3 className="text-lg font-semibold mt-6">
            Acceptance of the Rules:
          </h3>
          <p className="text-md mb-2">
            Access to the Platform or any of its components is strictly conditional upon the unreserved acceptance of these terms. If the User does not agree with any of the conditions, they must immediately refrain from using the services. Continued use of the system will be interpreted as tacit, voluntary, and definitive acceptance of all applicable rules.
          </p>

          <h4 className="text-base mb-2 mt-2">
            Nature of the Service and “Current State”
          </h4>
          <p className="text-md mb-2">
            The Platform is provided "as is" and "as available." Neither SEGIB nor the development team guarantees that the service will be uninterrupted, error-free, accurate, or completely secure. The User acknowledges that the software is inherently susceptible to technical failures and voluntarily assumes all risks associated with its use.
          </p>

          <h4 className="text-base mb-2 mt-2">
            Explicit Waiver of Claims for Damages
          </h4>
          <p className="text-md mb-2">
            By accepting these terms, the User irrevocably, fully, and absolutely waives any right to bring any future claim, demand, or legal action against SEGIB, the development team, its affiliates, or collaborators, for the following reasons:
          </p>
          <ul className="list text-md">
            <li>
              Direct or indirect damages: Including loss of data, loss of profits, or business interruption.
            </li>
            <li>
              Moral or material damages: Resulting from system failures, security vulnerabilities, or loss of information.
            </li>
            <li>
              <p className="mb-4">
                Third-party errors: Any damage caused by external services integrated into the Platform.
              </p>
              <p>
                <strong>Critical Note:</strong> Under no circumstances shall the Developer be liable to the User for any damages or losses, even if previously advised of the possibility of such damages.
              </p>
            </li>
          </ul>

          <h3 className="text-lg font-semibold mt-4">
            Indemnification
          </h3>
          <p className="text-md mb-2">
            The User agrees to indemnify and hold harmless SEGIB, the development team, and its collaborators from any third-party claims arising from the User’s use of the Platform or from any breach of these terms.
          </p>

          <h3 className="text-lg font-semibold mt-4">
            Intellectual Property
          </h3>
          <p className="text-md mb-2">
            The intellectual property of <strong>Aiuda</strong> belongs to the seven members of the development team; therefore, it is a collaborative work by the team identified in the “Identification” section.
          </p>
          <p className="text-md mb-2">
            The licensing scheme chosen for <strong>Aiuda</strong> is Creative Commons, which preserves the intellectual property of the original product in the individuals already identified.
          </p>

          <h3 className="text-lg font-semibold mt-4">
            Permitted and Prohibited Use
          </h3>
          <p className="text-md mb-2">
            <strong>Aiuda</strong> was initially designed as a tool to provide accessibility improvements for university faculty in countries that are part of SEGIB. However, as an open-source and free tool, it may be adopted by any educational institution or similar organizations.
          </p>
          <p className="text-md mb-2">
            <strong>Aiuda</strong> uses a Creative Commons license and grants permissions to share and adapt the source code. “Share” allows copying and redistributing the material in any medium or format. “Adapt” allows remixing, transforming, and building upon the material based on this project.
          </p>
          <p className="text-md mb-2">
            These permitted uses are subject to the following restrictions:
          </p>
          <p className="text-md mb-2">
            <strong>Attribution (BY):</strong> You must give appropriate credit to the development team and SEGIB, provide a link to the license, and indicate if changes were made. You may do so in any reasonable manner, but not in any way that suggests the licensor endorses you or your use.
          </p>
          <p className="text-md mb-2">
            <strong>Non-Commercial (NC):</strong> The material may not be used for commercial purposes, neither the original nor derivative works.
          </p>
          <p className="text-md mb-2">
            <strong>ShareAlike (SA):</strong> If you remix, transform, or build upon the material, you must distribute your contributions under the same license as the original.
          </p>
          <p className="text-md mb-2">
            The use of this application to create derivative works containing malware or mechanisms that enable the collection of confidential information from individuals—including names, email addresses, and virtual assets used (presentations, audio, videos, etc.)—is strictly prohibited.
          </p>
          <p className="text-md mb-2">
            It may not be used to distribute or store offensive or illegal content, or content that puts infrastructure or individuals at risk within the organizations where it is used or among its users, wherever they may be.
          </p>

          <h3 className="text-lg font-semibold mt-4">
            Acceptable Use Clause
          </h3>
          <p className="text-md mb-2">
            The use of the platform to create, store, distribute, or promote illegal or offensive content, or content that may endanger the safety of individuals, systems, or infrastructure, is not permitted.
          </p>
          <p className="text-md mb-2">
            This includes, but is not limited to, materials that:
          </p>
          <ul className="list text-md">
            <li>
              promote, incite, or legitimize hatred, violence, or discrimination against individuals or groups based on attributes such as origin, nationality, ethnicity, gender, gender identity, sexual orientation, religion, age, disability, or other personal or social conditions;
            </li>
            <li>
              contain threats, harassment, abuse, or any form of symbolic or physical violence;
            </li>
            <li>
              encourage illegal activities or behaviors that violate fundamental human rights;
            </li>
            <li>
              involve the dissemination of content that may cause physical, psychological, social, or reputational harm to individuals, communities, or organizations.
            </li>
          </ul>
          <p className="text-md mb-2">
            These restrictions apply regardless of the format, medium, or geographic location of the users.
          </p>
          <p className="text-md mb-2">
            The interpretation of these provisions shall be carried out in accordance with applicable regulations and principles of respect, inclusion, and non-discrimination.
          </p>

          <h3 className="text-lg font-semibold mt-4">
            Changes to Licensing
          </h3>
          <p className="text-md mb-2">
            SEGIB reserves the right to modify the licensing conditions in accordance with the technical and legal evolution of the tool. Continued use of the application after such changes implies acceptance of the new terms. For dispute resolution, the parties expressly agree to submit to the laws and courts of the city where the implementing University establishes its domicile, irrevocably waiving any other jurisdiction or venue.
          </p>

          <img src={getPublicAssetUrl("assets/by-nc-sa.png")} alt="Creative Commons License" className="logo-footer2"/>

          <p className="text-md mt-4 mb-2">
            Prepared by Darío Riquelme Z. <br />
            Reviewed by Ana Abac
          </p>
        </div>
      </div>
    </div>
  )
}