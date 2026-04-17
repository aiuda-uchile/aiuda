import { t } from "../../i18n/i18n"

export default function Terms({ onClose }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-xl w-full
          max-w-lg md:max-w-2xl lg:max-w-3xl
          max-h-[80vh] flex flex-col" onClick={(e) => e.stopPropagation()}>

        <h2 className="text-xl font-bold mb-4 px-10 pt-10">
          {t("terms-title")}
        </h2>
        <div className="px-6 overflow-y-auto mx-auto wp-95">
          <p className="text-lg font-semibold mb-4">
            {t("terms-subtitle")}
          </p>
          <p className="text-base">
            {t("terms-intro")}
          </p>
          <h3 className="text-lg font-semibold mt-4">
            {t("terms-id-title")}
          </h3>
          <p className="text-md mb-2">
            {t("terms-id-1")}
          </p>
          <p className="text-md mb-2">
            {t("terms-id-2")}
          </p>
          <p className="text-md mb-2">
            {t("terms-id-3")}
          </p>
          <p className="text-md mb-2">
            {t("terms-id-4")}
          </p>
          <p className="text-md mb-2">
            {t("terms-id-5")}
          </p>
          <p className="text-md mb-2">
            Paseo de Recoletos, 8 <br />
            28001 Madrid, España <br />
            Teléfono: (+34) 915 901 980 <br />
            info@segib.org
          </p>
          <h3 className="text-lg font-semibold mt-6">
            {t("terms-accept-title")}
          </h3>
          <p className="text-md mb-2">
            {t("terms-accept-text")}
          </p>
          <h4 className="text-base mb-2 mt-2">
            {t("terms-nature-title")}
          </h4>
          <p className="text-md mb-2">
            {t("terms-nature-text")}
          </p>
          <h4 className="text-base mb-2 mt-2">
            {t("terms-waiver-title")}
          </h4>
          <p className="text-md mb-2">
            {t("terms-waiver-intro")}
          </p>
          <ul className="list text-md">
            <li>
              <strong>{t("terms-waiver-1-title")}</strong> {t("terms-waiver-1-text")}
            </li>
            <li>
              <strong>{t("terms-waiver-2-title")}</strong> {t("terms-waiver-2-text")}
            </li>
            <li>
              <p className="mb-4"><strong>{t("terms-waiver-3-title")}</strong> {t("terms-waiver-3-text")}</p>
              <p>
                <strong>{t("terms-waiver-note")}</strong>
              </p>
            </li>
          </ul>
        </div>
        <div className="flex justify-end p-6">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-color-primary text-white"
          >
            {t("terms-close")}
          </button>
        </div>
      </div>
    </div>
  )
}
