import { useState, useRef, useEffect } from 'react';
import {
  Box,
  VStack,
  HStack,
  Input,
  Button,
  Text,
  Flex,
} from '@chakra-ui/react';
import { useToast } from '@chakra-ui/toast';
import { useStore } from '../store/useStore';
import { streamChat } from '../api/api';
import { ChatMessage } from '../types';

export const ChatInterface = () => {
  const { messages, documents, modelConfig, isLoading, addMessage, setLoading, setError } = useStore();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const toast = useToast();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || documents.length === 0) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

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
            lastMessage.content = assistantMessage;
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
    <VStack h="100%" gap={4}>
      <Box
        flex={1}
        w="100%"
        overflowY="auto"
        p={4}
        bg="gray.50"
        borderRadius="md"
      >
        {messages.map((message: ChatMessage, index: number) => (
          <Flex
            key={index}
            mb={4}
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
              <Text>{message.content}</Text>
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
        <HStack>
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
