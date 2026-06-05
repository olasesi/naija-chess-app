import { Link } from 'expo-router';
import { View, Text } from 'react-native';

export default function HomeScreen() {
  return (
    <View className="flex-1 items-center justify-center bg-white px-6">
      <Text className="text-4xl font-heading text-primary-700 mb-2">Hello 👋</Text>
      <Text className="text-base text-gray-500 text-center mb-8">
        Your Expo boilerplate is ready. Start building!
      </Text>
      <Link href="/explore" className="text-primary-500 font-semibold text-sm">
        Go to Explore →
      </Link>
    </View>
  );
}
