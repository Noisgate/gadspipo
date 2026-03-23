import { Button } from "@adsmcp/ui";
import {
  clearSavedSearchCampaignDraftAction,
  saveSearchCampaignDraftAction,
} from "./actions";

type SearchDraftActionsProps = {
  canSave: boolean;
  hasSavedDraft: boolean;
};

export function SearchDraftActions({
  canSave,
  hasSavedDraft,
}: SearchDraftActionsProps) {
  return (
    <div className="draft-actions">
      <form action={saveSearchCampaignDraftAction}>
        <Button disabled={!canSave} type="submit">
          Salvar snapshot do draft
        </Button>
      </form>

      <form action={clearSavedSearchCampaignDraftAction}>
        <Button disabled={!hasSavedDraft} type="submit" variant="secondary">
          Limpar draft salvo
        </Button>
      </form>
    </div>
  );
}
