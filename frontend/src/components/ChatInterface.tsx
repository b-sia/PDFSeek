import { useState, useRef, useEffect } from 'react';
import {
  Box,
  VStack,
  HStack,
  Input,
  Button,
  Text,
  Flex,
  useToast,
} from '@chakra-ui/react';
import { useStore } from '../store/useStore';
import { streamChat } from '../api/api';
import { ChatMessage } from '../types';

export const ChatInterface = () => {
  const { messages, documents, modelConfig, isLoading, addMessage, setLoading, setError, clearMessages } = useStore();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const toast = useToast();

  // Clear chat history on component mount (page refresh)
  useEffect(() => {
    clearMessages();
  }, []);

  // Scroll to bottom whenever messages change
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || documents.length === 0) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    // Add user message to history
    addMessage(userMessage);
    setInput('');
    setLoading(true);

    try {
      let assistantMessage = '';
      await streamChat(
        input,
        modelConfig.model_type,
        documents.map(doc => doc.document_id),
        (chunk) => {
          assistantMessage += chunk;
          // Update the last message if it's from assistant, or create new one
          const lastMessage = messages[messages.length - 1];
          if (lastMessage?.role === 'assistant') {
            // Create a new message object to trigger state update
            const updatedMessage: ChatMessage = {
              ...lastMessage,
              content: assistantMessage,
            };
            addMessage(updatedMessage);
          } else {
            addMessage({
              role: 'assistant',
              content: assistantMessage,
              timestamp: new Date(),
            });
          }
        }
      );
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to get response');
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to get response',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <VStack h="100%" w="100%" spacing={4} justify="space-between">
      <Box
        ref={chatContainerRef}
        flex={1}
        w="100%"
        overflowY="auto"
        p={4}
        bg="gray.50"
        borderRadius="md"
        minH="calc(100vh - 200px)"
        maxH="calc(100vh - 200px)"
        display="flex"
        flexDirection="column"
        flexGrow={1}
        css={{
          '&::-webkit-scrollbar': {
            width: '4px',
          },
          '&::-webkit-scrollbar-track': {
            width: '6px',
            background: 'transparent',
          },
          '&::-webkit-scrollbar-thumb': {
            background: 'gray.300',
            borderRadius: '24px',
          },
          '&::-webkit-scrollbar-thumb:hover': {
            background: 'gray.400',
          },
        }}
      >
        {messages.map((message: ChatMessage, index: number) => (
          <Flex
            key={index}
            mb={4}
            w="100%"
            justify={message.role === 'user' ? 'flex-end' : 'flex-start'}
          >
            <Box
              maxW="70%"
              bg={message.role === 'user' ? 'blue.500' : 'white'}
              color={message.role === 'user' ? 'white' : 'black'}
              p={3}
              borderRadius="lg"
              boxShadow="sm"
            >
              <Text whiteSpace="pre-wrap">{message.content}</Text>
              {message.sources && (
                <Box mt={2} fontSize="sm" color="gray.500">
                  <Text fontWeight="bold">Sources:</Text>
                  {message.sources.map((source, idx) => (
                    <Text key={idx}>{source}</Text>
                  ))}
                </Box>
              )}
            </Box>
          </Flex>
        ))}
        <div ref={messagesEndRef} />
      </Box>

      <form onSubmit={handleSubmit} style={{ width: '100%' }}>
        <HStack w="100%">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about your documents..."
            disabled={isLoading || documents.length === 0}
          />
          <Button
            type="submit"
            colorScheme="blue"
            isLoading={isLoading}
            disabled={!input.trim() || documents.length === 0}
          >
            Send
          </Button>
        </HStack>
      </form>
    </VStack>
  );
};
