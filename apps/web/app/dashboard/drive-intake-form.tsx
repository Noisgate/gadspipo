import { campaignObjectiveOptions } from "@adsmcp/domain";
import { Button } from "@adsmcp/ui";
import type { WorkspaceDriveIntake } from "@adsmcp/domain";
import {
  clearDriveIntakeAction,
  saveDriveIntakeAction,
} from "./actions";

type DriveIntakeFormProps = {
  defaultValues: WorkspaceDriveIntake;
};

export function DriveIntakeForm({ defaultValues }: DriveIntakeFormProps) {
  return (
    <div className="intake-stack">
      <form action={saveDriveIntakeAction} className="intake-form">
        <label className="field">
          <span className="field-label">Customer ID do Google Ads</span>
          <input
            className="text-input"
            defaultValue={defaultValues.googleAdsCustomerId}
            name="googleAdsCustomerId"
            placeholder="1234567890"
            type="text"
          />
        </label>

        <label className="field">
          <span className="field-label">Link ou ID da pasta do Google Drive</span>
          <input
            className="text-input"
            defaultValue={defaultValues.folderInput}
            name="folderInput"
            placeholder="https://drive.google.com/drive/folders/..."
            type="text"
          />
        </label>

        <label className="field">
          <span className="field-label">Objetivo principal</span>
          <select
            className="text-input"
            defaultValue={defaultValues.objective}
            name="objective"
          >
            {campaignObjectiveOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>

        <label className="field">
          <span className="field-label">Resumo da oferta</span>
          <textarea
            className="text-area"
            defaultValue={defaultValues.offerSummary}
            name="offerSummary"
            placeholder="Explique em poucas linhas o que está sendo vendido e o principal diferencial."
            rows={4}
          />
        </label>

        <label className="field">
          <span className="field-label">Landing page principal</span>
          <input
            className="text-input"
            defaultValue={defaultValues.landingPageUrl}
            name="landingPageUrl"
            placeholder="https://empresa.com/oferta"
            type="url"
          />
        </label>

        <label className="field">
          <span className="field-label">Notas e restrições</span>
          <textarea
            className="text-area"
            defaultValue={defaultValues.notes}
            name="notes"
            placeholder="Tom de voz, termos proibidos, diferenciais, região alvo ou qualquer contexto útil."
            rows={4}
          />
        </label>

        <div className="hero-actions">
          <Button type="submit">Salvar contexto da campanha</Button>
        </div>
      </form>

      <form action={clearDriveIntakeAction}>
        <Button type="submit" variant="secondary">
          Limpar contexto salvo
        </Button>
      </form>
    </div>
  );
}
