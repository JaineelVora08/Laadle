import { useQuery } from '@tanstack/react-query';
import axiosInstance from './axiosInstance';

export function useProfile(userId) {
    return useQuery({
        queryKey: ['profile', userId],
        queryFn: () => axiosInstance.get(`/api/profile/${userId}/`).then((r) => r.data),
        enabled: Boolean(userId),
        staleTime: 5 * 60 * 1000,
        gcTime: 30 * 60 * 1000,
    });
}

export function usePendingQueries(seniorId) {
    return useQuery({
        queryKey: ['pending', seniorId],
        queryFn: () => axiosInstance.get(`/api/query/pending/senior/${seniorId}/`).then((r) => r.data),
        enabled: Boolean(seniorId),
        staleTime: 30 * 1000,
        refetchInterval: 60 * 1000,
    });
}

export function useStudentQueries(studentId) {
    return useQuery({
        queryKey: ['studentQueries', studentId],
        queryFn: () => axiosInstance.get(`/api/query/student/${studentId}/`).then((r) => r.data),
        enabled: Boolean(studentId),
        staleTime: 30 * 1000,
        refetchInterval: 60 * 1000,
    });
}

export function useDomains() {
    return useQuery({
        queryKey: ['domains'],
        queryFn: () => axiosInstance.get('/api/domains/all/').then((r) => r.data),
        staleTime: 30 * 60 * 1000,
        gcTime: 60 * 60 * 1000,
    });
}
