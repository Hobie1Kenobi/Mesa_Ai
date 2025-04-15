import { useRef, useState, useEffect } from 'react';
import { Box } from '@chakra-ui/react';
import * as THREE from 'three';
import { Canvas, useFrame, extend, Object3DNode } from '@react-three/fiber';
import { Text, OrbitControls, useCursor } from '@react-three/drei';

// Types for our data tiles
interface DataTile {
  id: string;
  title: string;
  artist?: string;
  rightsId?: string;
  registrationDate?: string;
  isrc?: string;
  iswc?: string;
  status: 'registered' | 'pending' | 'failed';
  position: [number, number, number];
  rotation: [number, number, number];
}

// Floating Tile component
function FloatingTile({ 
  data, 
  position, 
  rotation 
}: { 
  data: DataTile; 
  position: [number, number, number]; 
  rotation: [number, number, number];
}) {
  const meshRef = useRef<THREE.Mesh>(null);
  const [hovered, setHover] = useState(false);
  const [clicked, setClicked] = useState(false);
  
  // Handle cursor changes
  useCursor(hovered);
  
  // Animate rotation
  useFrame((state, delta) => {
    if (meshRef.current) {
      meshRef.current.rotation.x += delta * 0.2;
      meshRef.current.rotation.y += delta * 0.1;
      
      // Slight floating movement
      meshRef.current.position.y += Math.sin(state.clock.elapsedTime) * 0.002;
    }
  });

  // Material colors based on status
  const getColor = () => {
    switch (data.status) {
      case 'registered': return new THREE.Color(0x4299e1); // blue
      case 'pending': return new THREE.Color(0xecc94b); // yellow
      case 'failed': return new THREE.Color(0xe53e3e); // red
      default: return new THREE.Color(0x4299e1);
    }
  };

  return (
    <group position={position} rotation={rotation}>
      <mesh
        ref={meshRef}
        onPointerOver={() => setHover(true)}
        onPointerOut={() => setHover(false)}
        onClick={() => setClicked(!clicked)}
        scale={clicked ? 1.2 : 1}
      >
        <boxGeometry args={[3, 2, 0.1]} />
        <meshPhysicalMaterial
          color={getColor()}
          transparent={true}
          opacity={0.65}
          metalness={0.5}
          roughness={0.3}
          transmission={0.6} // Makes it glass-like
          clearcoat={1}
          clearcoatRoughness={0.1}
        />
      </mesh>
      
      {/* Front text */}
      <Text
        position={[0, 0.5, 0.06]}
        fontSize={0.2}
        color="#ffffff"
        anchorX="center"
        anchorY="middle"
        maxWidth={2.5}
      >
        {data.title}
      </Text>
      
      <Text
        position={[0, 0.2, 0.06]}
        fontSize={0.15}
        color="#ffffff"
        anchorX="center"
        anchorY="middle"
      >
        {data.artist || "Unknown Artist"}
      </Text>
      
      <Text
        position={[0, -0.1, 0.06]}
        fontSize={0.12}
        color="#ffffff"
        anchorX="center"
        anchorY="middle"
      >
        Rights ID: {data.rightsId?.substring(0, 8) || "Pending"}
      </Text>
      
      <Text
        position={[0, -0.4, 0.06]}
        fontSize={0.12}
        color="#ffffff"
        anchorX="center"
        anchorY="middle"
      >
        Status: {data.status}
      </Text>
    </group>
  );
}

// Scene component that contains all tiles
function FloatingScene({ data }: { data: DataTile[] }) {
  return (
    <>
      <ambientLight intensity={0.5} />
      <pointLight position={[10, 10, 10]} intensity={1} />
      <pointLight position={[-10, -10, -10]} intensity={0.5} />
      
      {data.map((tile) => (
        <FloatingTile 
          key={tile.id} 
          data={tile} 
          position={tile.position} 
          rotation={tile.rotation} 
        />
      ))}
      
      <OrbitControls 
        enableZoom={true} 
        enablePan={true}
        minDistance={5}
        maxDistance={20}
      />
    </>
  );
}

// Main component
export default function FloatingBubbleChart({ 
  data,
  height = "600px"
}: { 
  data: any[];
  height?: string;
}) {
  // Transform data into the format needed for visualization
  const transformedData: DataTile[] = data.map((item, index) => {
    // Calculate position in a circular pattern
    const angle = (index / data.length) * Math.PI * 2;
    const radius = 5;
    const x = Math.cos(angle) * radius;
    const z = Math.sin(angle) * radius;
    const y = Math.sin(index * 0.5) * 2;
    
    return {
      id: item.id || `item-${index}`,
      title: item.title || "Untitled",
      artist: item.artist,
      rightsId: item.rightsId,
      registrationDate: item.timestamp,
      isrc: item.isrc,
      iswc: item.iswc,
      status: item.status || "pending",
      position: [x, y, z],
      rotation: [
        Math.random() * 0.3 - 0.15,
        Math.random() * 0.3 - 0.15,
        Math.random() * 0.3 - 0.15
      ],
    };
  });

  return (
    <Box w="100%" h={height} borderRadius="md" overflow="hidden">
      <Canvas camera={{ position: [0, 0, 10], fov: 50 }}>
        <FloatingScene data={transformedData} />
      </Canvas>
    </Box>
  );
} 