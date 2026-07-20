import ChatInterface from './components/ChatInterface';

function App() {
  return (
    <div className="min-h-screen bg-black text-white flex items-center justify-center p-4">
      <div className="w-full max-w-5xl h-[90vh] flex flex-col">
        <ChatInterface />
      </div>
    </div>
  );
}

export default App;
