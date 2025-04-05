import { ChakraProvider, Box, Grid, GridItem } from '@chakra-ui/react';
import { FileUploader } from './components/FileUploader';
import { ChatInterface } from './components/ChatInterface';
import { ModelConfigPanel } from './components/ModelConfigPanel';

function App() {
  return (
    <ChakraProvider>
      <Box h="100vh" p={4}>
        <Grid
          templateColumns="300px 1fr"
          templateRows="1fr"
          gap={4}
          h="100%"
        >
          <GridItem>
            <Box p={4} bg="white" borderRadius="md" boxShadow="sm">
              <ModelConfigPanel />
            </Box>
            <Box mt={4} p={4} bg="white" borderRadius="md" boxShadow="sm">
              <FileUploader />
            </Box>
          </GridItem>
          <GridItem>
            <Box p={4} bg="white" borderRadius="md" boxShadow="sm" h="100%">
              <ChatInterface />
            </Box>
          </GridItem>
        </Grid>
      </Box>
    </ChakraProvider>
  );
}

export default App;
