/**
 * Zustand store for query state.
 * State: { queries: QuerySubmitResponse[], activeQuery: QuerySubmitResponse | null }
 * Actions: addQuery(q), setActiveQuery(q), resolveQuery(queryId, finalResponse)
 */
import { create } from 'zustand';

export const useQueryStore = create((set, get) => ({
    queries: [],
    activeQuery: null,

    addQuery: (query) =>
        set((state) => ({
            queries: [...state.queries, query],
            activeQuery: query,
        })),

    setActiveQuery: (query) => set({ activeQuery: query }),

    resolveQuery: (queryId, finalResponse) =>
        set((state) => ({
            queries: state.queries.map((q) =>
                q.query_id === queryId
                    ? { ...q, ...finalResponse, is_resolved: true }
                    : q
            ),
            activeQuery:
                state.activeQuery?.query_id === queryId
                    ? { ...state.activeQuery, ...finalResponse, is_resolved: true }
                    : state.activeQuery,
        })),
}));
