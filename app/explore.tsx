import { View, Text } from 'react-native';

export default function ExploreScreen() {
  return (
    <View className="flex-1 items-center justify-center bg-white px-6">
      <Text className="text-2xl font-heading text-primary-700 mb-2">Explore</Text>
      <Text className="text-base text-gray-500 text-center">Discover chess content here</Text>
    </View>
  );
}
