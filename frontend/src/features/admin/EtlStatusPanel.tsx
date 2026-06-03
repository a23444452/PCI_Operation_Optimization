import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2, AlertCircle, Play } from "lucide-react";
import api from "@/lib/api";

interface EtlJob {
  id: number;
  job_type: string;
  started_at: string;
  finished_at: string | null;
  status: "completed" | "failed" | "running" | "skipped";
  records_count: number | null;
  error_msg: string | null;
}

const STATUS_BADGE: Record<string, string> = {
  completed: "bg-green-100 text-green-800",
  failed: "bg-red-100 text-red-800",
  running: "bg-yellow-100 text-yellow-800",
  skipped: "bg-gray-100 text-gray-800",
};

const JOB_TYPES = ["offload_sync", "coa_sync", "daily_analysis", "risk_assessment"];

export function EtlStatusPanel() {
  const queryClient = useQueryClient();

  const {
    data: jobs,
    isLoading,
    error,
  } = useQuery<EtlJob[]>({
    queryKey: ["admin-etl-status"],
    queryFn: async () => {
      const res = await api.get("/admin/etl-status");
      return res.data.data;
    },
    refetchInterval: 30000,
  });

  const triggerMutation = useMutation({
    mutationFn: async (jobType: string) => {
      const res = await api.post(`/admin/etl/trigger/${jobType}`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-etl-status"] });
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-gray-500">
        <Loader2 className="h-5 w-5 animate-spin" />
        <span>Loading ETL status...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 rounded-md border border-red-200 bg-red-50 p-4 text-red-700">
        <AlertCircle className="h-5 w-5" />
        <span>Failed to load ETL status. Please try again.</span>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">ETL Status</h3>
        <div className="flex items-center gap-2">
          {JOB_TYPES.map((jobType) => (
            <button
              key={jobType}
              onClick={() => triggerMutation.mutate(jobType)}
              disabled={triggerMutation.isPending}
              className="inline-flex items-center gap-1 rounded-md border border-gray-300 bg-white px-2.5 py-1.5 text-xs font-medium text-gray-700 shadow-sm hover:bg-gray-50 disabled:opacity-50"
              title={`Trigger ${jobType}`}
            >
              <Play className="h-3 w-3" />
              {jobType}
            </button>
          ))}
        </div>
      </div>

      {triggerMutation.isError && (
        <div className="flex items-center gap-2 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          <AlertCircle className="h-4 w-4" />
          <span>Failed to trigger job.</span>
        </div>
      )}

      {triggerMutation.isSuccess && (
        <div className="flex items-center gap-2 rounded-md border border-green-200 bg-green-50 p-3 text-sm text-green-700">
          <span>Job triggered successfully.</span>
        </div>
      )}

      <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Job Type
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Started At
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Finished At
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Status
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Records
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Error
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white">
            {jobs?.map((job) => (
              <tr key={job.id} className="hover:bg-gray-50">
                <td className="whitespace-nowrap px-4 py-3 text-sm font-medium text-gray-900">
                  {job.job_type}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-600">
                  {job.started_at}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-600">
                  {job.finished_at ?? "-"}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-sm">
                  <span
                    className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_BADGE[job.status] ?? "bg-gray-100 text-gray-800"}`}
                  >
                    {job.status}
                  </span>
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-600">
                  {job.records_count !== null ? job.records_count.toLocaleString() : "-"}
                </td>
                <td className="max-w-xs truncate px-4 py-3 text-sm text-red-600" title={job.error_msg ?? ""}>
                  {job.error_msg ?? "-"}
                </td>
              </tr>
            ))}
            {(!jobs || jobs.length === 0) && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-sm text-gray-500">
                  No ETL jobs found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
