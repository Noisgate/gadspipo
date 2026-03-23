import { Button } from "@adsmcp/ui";
import { signOutAction } from "../auth/actions";

export function SignOutForm() {
  return (
    <form action={signOutAction}>
      <Button type="submit" variant="secondary">
        Sair
      </Button>
    </form>
  );
}
