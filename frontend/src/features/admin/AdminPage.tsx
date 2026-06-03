import { EtlStatusPanel } from "./EtlStatusPanel";
import { UsersPage } from "./UsersPage";

export function AdminPage() {
  return (
    <div className="space-y-8">
      <h2 className="text-2xl font-bold text-gray-900">Administration</h2>

      <section>
        <EtlStatusPanel />
      </section>

      <hr className="border-gray-200" />

      <section>
        <UsersPage />
      </section>
    </div>
  );
}
