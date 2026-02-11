"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { fetchAPI } from "@/lib/api";
import { TrendingUp, TrendingDown, Minus, AlertTriangle } from "lucide-react";

interface Indicator {
  id: number;
  name: string;
  category: string;
  unit: string;
}

export default function DashboardContent() {
  const [indicators, setIndicators] = useState<Indicator[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const data = await fetchAPI<Indicator[]>("/api/indicators?limit=5");
        setIndicators(data);
      } catch (err) {
        setError("Failed to load indicators");
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Card className="w-full max-w-md border-destructive">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-destructive">
              <AlertTriangle className="h-5 w-5" />
              Error
            </CardTitle>
            <CardDescription>{error}</CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight mb-2">Economy Tracker Dashboard</h1>
        <p className="text-muted-foreground">
          Monitor key macroeconomic indicators and get actionable insights
        </p>
      </div>

      {/* Key Indicators Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {indicators.map((indicator) => (
          <Card key={indicator.id}>
            <CardHeader className="pb-2">
              <CardDescription>{indicator.category}</CardDescription>
              <CardTitle className="text-lg">{indicator.name}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-2xl font-bold">--</div>
                  <p className="text-xs text-muted-foreground">{indicator.unit || "index"}</p>
                </div>
                <Badge variant="outline">
                  <Minus className="h-3 w-3 mr-1" />
                  No data
                </Badge>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Insights Section */}
      <Card>
        <CardHeader>
          <CardTitle>Economic Insights</CardTitle>
          <CardDescription>AI-powered analysis of economic trends</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="border-l-4 border-blue-500 pl-4">
              <h4 className="font-semibold mb-1">What Changed?</h4>
              <p className="text-sm text-muted-foreground">
                Connect to a data source to see insights and analysis.
              </p>
            </div>
            <div className="border-l-4 border-green-500 pl-4">
              <h4 className="font-semibold mb-1">Why It Matters?</h4>
              <p className="text-sm text-muted-foreground">
                Get context on economic indicators and their impact.
              </p>
            </div>
            <div className="border-l-4 border-orange-500 pl-4">
              <h4 className="font-semibold mb-1">Risk Signals</h4>
              <p className="text-sm text-muted-foreground">
                Monitor warning signs and potential concerns.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Regime Indicator */}
      <Card>
        <CardHeader>
          <CardTitle>Economic Regime</CardTitle>
          <CardDescription>Current economic cycle classification</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <Badge variant="secondary" className="text-lg px-4 py-2">
                Unknown
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground flex-1">
              Connect data sources to see regime classification
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
