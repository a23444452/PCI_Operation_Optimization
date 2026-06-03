import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";

export interface Plant {
  id: number;
  name: string;
  code: string;
}

export function usePlants() {
  return useQuery<Plant[]>({
    queryKey: ["plants"],
    queryFn: async () => {
      const res = await api.get("/offload/plants");
      return res.data.data;
    },
  });
}
