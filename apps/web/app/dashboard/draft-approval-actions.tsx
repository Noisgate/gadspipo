import { Button } from "@adsmcp/ui";
import {
  approveSearchCampaignDraftForPublicationAction,
  clearSearchCampaignDraftApprovalAction,
  requestSearchCampaignDraftChangesAction,
  submitSearchCampaignDraftForApprovalAction,
} from "./draft-approval-server-actions";

type DraftApprovalActionsProps = {
  approvalStatus: "not_requested" | "pending_review" | "approved" | "changes_requested";
  hasApprovalRequest: boolean;
  hasSavedDraft: boolean;
};

function getPrimaryLabel(status: DraftApprovalActionsProps["approvalStatus"]) {
  if (status === "approved") {
    return "Atualizar aprovacao";
  }

  if (status === "changes_requested") {
    return "Reenviar para aprovacao";
  }

  return "Enviar para aprovacao";
}

export function DraftApprovalActions({
  approvalStatus,
  hasApprovalRequest,
  hasSavedDraft,
}: DraftApprovalActionsProps) {
  if (approvalStatus === "pending_review") {
    return (
      <div className="draft-actions">
        <form action={approveSearchCampaignDraftForPublicationAction}>
          <Button type="submit">Aprovar para publicar</Button>
        </form>

        <form action={requestSearchCampaignDraftChangesAction}>
          <Button type="submit" variant="secondary">
            Solicitar ajustes
          </Button>
        </form>

        <form action={clearSearchCampaignDraftApprovalAction}>
          <Button type="submit" variant="secondary">
            Limpar aprovacao
          </Button>
        </form>
      </div>
    );
  }

  return (
    <div className="draft-actions">
      <form action={submitSearchCampaignDraftForApprovalAction}>
        <Button disabled={!hasSavedDraft} type="submit">
          {getPrimaryLabel(approvalStatus)}
        </Button>
      </form>

      <form action={clearSearchCampaignDraftApprovalAction}>
        <Button
          disabled={!hasApprovalRequest}
          type="submit"
          variant="secondary"
        >
          Limpar aprovacao
        </Button>
      </form>
    </div>
  );
}
