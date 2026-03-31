'use client';

import { useEffect } from 'react';
import { Sidebar } from '../../components/layout/Sidebar';
import { Header } from '../../components/layout/Header';
import { ChatArea } from '../../components/chat/ChatArea';
import { Composer } from '../../components/chat/Composer';
import { useAgentStore } from '../../store/useAgentStore';

export default function ChatInterface() {
	const { setSessionId, sessionId } = useAgentStore();

	// Initialize session on first load
	useEffect(() => {
		if (!sessionId) {
			setSessionId(crypto.randomUUID());
		}
	}, [sessionId, setSessionId]);

	return (
		<main className="flex h-screen w-full overflow-hidden bg-white text-zinc-900 selection:bg-emerald-200">
			<Sidebar />
			<div className="flex h-full min-w-0 flex-1 flex-col bg-white">
				<Header />
				<ChatArea />
				<Composer />
			</div>
		</main>
	);
}
