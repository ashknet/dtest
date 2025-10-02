"""
PAGINATION IMPLEMENTATION EXAMPLES FOR MAT GRAPHQL API (Python)
"""

import requests
import json
from typing import Dict, List, Optional, Any
import os


# ===================================================================
# OPTION 1: OFFSET-BASED PAGINATION (SIMPLE)
# ===================================================================

def fetch_all_engagements_offset_based(
    client_id: str,
    fiscal_year: str,
    page_size: int = 500,
    mat_endpoint: str = None,
    api_token: str = None
) -> Dict[str, Any]:
    """
    Fetch all engagements using offset-based pagination.
    
    Args:
        client_id: Client ID to search for
        fiscal_year: Fiscal year to search for
        page_size: Number of engagements per page (default: 500)
        mat_endpoint: MAT GraphQL API endpoint URL
        api_token: API authentication token
        
    Returns:
        Complete response with all engagements
    """
    
    query = """
    query MATGlobalClientRequest($clientId: String!, $fiscalYear: String!, $skip: Int!, $take: Int!) {
      clients(where:{clientId:{eq:$clientId}}) {
        clientFiscalYear
        parentClientId
        clientId
        clientName
        clientProfiles(where: {clientAuditYear:{eq: $fiscalYear}}) {
          clientProfileId
          clientAuditYear
          engagements(
            where: {
              isNoLongerPerforming : {eq: false}
              isDeleted : {eq: false}
              isTerminated : {eq: false}
              isInvalidated : {eq: false}
              engagementTypeId: { neq: 6 }
              serviceTypeId: { nin: [10, 11, 12] }
            }
            skip: $skip
            take: $take
          ) {
            engagementNumber
            engagementName
            engagementDescription
            engagementTypeName
            servicePeriodStartDate
            serviceName
            updatedDate
            isDeleted
            isTerminated
            isInvalidated
            isSpecialPurpose
            isNoLongerPerforming
            subjectMatterId
            subjectMatterName
            subjectMatterValue
            modelAuditRuleInsurance500Mln
            picAssigned
            parentEngagement {
              engagementNumber
              engagementName
              engagementTypeName
              serviceName
              isSpecialPurpose
              isDeleted
              isTerminated
              isInvalidated
              isNoLongerPerforming
              servicePeriodStartDate
              subjectMatterId
              subjectMatterName
              subjectMatterValue
              modelAuditRuleInsurance500Mln
              reportingEntity {
                entityName
                entityTypeId
                entityTypeName
                uISelectedTypeId
                uISelectedTypeName
                entityDerivedTypeId
                entityDerivedTypeName
              }
              pso {
                pSOName
                servicePeriodEnd
              }
            }
            pso {
              pSOName
              servicePeriodEnd
              industryId
              industryName
              issuingOfficeId
              regionId
              regionName
              sectorId
              sectorName
              officeName
              updatedDate
            }
            deliverables {
              deliverableSPSs {
                key
                value
              }
              updatedDate
            }
            reportingEntity {
              entityTypeId
              entityName
              entityTypeName
              entityDerivedTypeName
              entityDerivedTypeId
              uISelectedTypeId
            }
            spawnedEngagement {
              engagementNumber
            }
          }
        }
      }
    }
    """
    
    all_engagements = []
    skip = 0
    has_more = True
    client_data = None
    request_count = 0
    
    print(f"Starting paginated fetch for client {client_id}, fiscal year {fiscal_year}")
    print(f"Page size: {page_size}")
    
    while has_more:
        request_count += 1
        print(f"\n--- Request {request_count} ---")
        print(f"Fetching engagements {skip} to {skip + page_size - 1}...")
        
        variables = {
            "clientId": client_id,
            "fiscalYear": fiscal_year,
            "skip": skip,
            "take": page_size
        }
        
        try:
            # Make the GraphQL request
            response = make_graphql_request(
                query, 
                variables, 
                endpoint=mat_endpoint,
                token=api_token
            )
            
            # Extract data
            clients = response.get("data", {}).get("clients", [])
            
            if not clients:
                print("No clients found")
                break
            
            # Store client-level data from first request
            if not client_data:
                client_data = {
                    "clientFiscalYear": clients[0].get("clientFiscalYear"),
                    "parentClientId": clients[0].get("parentClientId"),
                    "clientId": clients[0].get("clientId"),
                    "clientName": clients[0].get("clientName"),
                    "clientProfileId": clients[0]["clientProfiles"][0].get("clientProfileId") if clients[0].get("clientProfiles") else None,
                    "clientAuditYear": clients[0]["clientProfiles"][0].get("clientAuditYear") if clients[0].get("clientProfiles") else None
                }
            
            client_profiles = clients[0].get("clientProfiles", [])
            engagements = client_profiles[0].get("engagements", []) if client_profiles else []
            
            print(f"Retrieved {len(engagements)} engagements")
            all_engagements.extend(engagements)
            print(f"Total engagements so far: {len(all_engagements)}")
            
            # Check if there are more results
            has_more = len(engagements) == page_size
            skip += page_size
            
        except Exception as e:
            print(f"Error on request {request_count}: {str(e)}")
            raise
    
    print(f"\n=== Fetch Complete ===")
    print(f"Total API requests: {request_count}")
    print(f"Total engagements retrieved: {len(all_engagements)}")
    
    # Reconstruct the full response
    return {
        "data": {
            "clients": [{
                "clientFiscalYear": client_data["clientFiscalYear"],
                "parentClientId": client_data["parentClientId"],
                "clientId": client_data["clientId"],
                "clientName": client_data["clientName"],
                "clientProfiles": [{
                    "clientProfileId": client_data["clientProfileId"],
                    "clientAuditYear": client_data["clientAuditYear"],
                    "engagements": all_engagements
                }]
            }]
        }
    }


# ===================================================================
# OPTION 2: CURSOR-BASED PAGINATION (RECOMMENDED FOR PRODUCTION)
# ===================================================================

def fetch_all_engagements_cursor_based(
    client_id: str,
    fiscal_year: str,
    page_size: int = 500,
    mat_endpoint: str = None,
    api_token: str = None
) -> Dict[str, Any]:
    """
    Fetch all engagements using cursor-based pagination.
    
    Args:
        client_id: Client ID to search for
        fiscal_year: Fiscal year to search for
        page_size: Number of engagements per page (default: 500)
        mat_endpoint: MAT GraphQL API endpoint URL
        api_token: API authentication token
        
    Returns:
        Complete response with all engagements
    """
    
    query = """
    query MATGlobalClientRequest($clientId: String!, $fiscalYear: String!, $first: Int!, $after: String) {
      clients(where:{clientId:{eq:$clientId}}) {
        clientFiscalYear
        parentClientId
        clientId
        clientName
        clientProfiles(where: {clientAuditYear:{eq: $fiscalYear}}) {
          clientProfileId
          clientAuditYear
          engagements(
            where: {
              isNoLongerPerforming : {eq: false}
              isDeleted : {eq: false}
              isTerminated : {eq: false}
              isInvalidated : {eq: false}
              engagementTypeId: { neq: 6 }
              serviceTypeId: { nin: [10, 11, 12] }
            }
            first: $first
            after: $after
          ) {
            edges {
              node {
                engagementNumber
                engagementName
                engagementDescription
                engagementTypeName
                servicePeriodStartDate
                serviceName
                updatedDate
                isDeleted
                isTerminated
                isInvalidated
                isSpecialPurpose
                isNoLongerPerforming
                subjectMatterId
                subjectMatterName
                subjectMatterValue
                modelAuditRuleInsurance500Mln
                picAssigned
                parentEngagement {
                  engagementNumber
                  engagementName
                  engagementTypeName
                  serviceName
                  isSpecialPurpose
                  isDeleted
                  isTerminated
                  isInvalidated
                  isNoLongerPerforming
                  servicePeriodStartDate
                  subjectMatterId
                  subjectMatterName
                  subjectMatterValue
                  modelAuditRuleInsurance500Mln
                  reportingEntity {
                    entityName
                    entityTypeId
                    entityTypeName
                    uISelectedTypeId
                    uISelectedTypeName
                    entityDerivedTypeId
                    entityDerivedTypeName
                  }
                  pso {
                    pSOName
                    servicePeriodEnd
                  }
                }
                pso {
                  pSOName
                  servicePeriodEnd
                  industryId
                  industryName
                  issuingOfficeId
                  regionId
                  regionName
                  sectorId
                  sectorName
                  officeName
                  updatedDate
                }
                deliverables {
                  deliverableSPSs {
                    key
                    value
                  }
                  updatedDate
                }
                reportingEntity {
                  entityTypeId
                  entityName
                  entityTypeName
                  entityDerivedTypeName
                  entityDerivedTypeId
                  uISelectedTypeId
                }
                spawnedEngagement {
                  engagementNumber
                }
              }
              cursor
            }
            pageInfo {
              hasNextPage
              endCursor
            }
            totalCount
          }
        }
      }
    }
    """
    
    all_engagements = []
    cursor = None
    has_next_page = True
    client_data = None
    request_count = 0
    total_count = None
    
    print(f"Starting cursor-based paginated fetch for client {client_id}, fiscal year {fiscal_year}")
    print(f"Page size: {page_size}")
    
    while has_next_page:
        request_count += 1
        print(f"\n--- Request {request_count} ---")
        print(f"Cursor: {cursor or 'null (first page)'}")
        
        variables = {
            "clientId": client_id,
            "fiscalYear": fiscal_year,
            "first": page_size,
            "after": cursor
        }
        
        try:
            # Make the GraphQL request
            response = make_graphql_request(
                query, 
                variables,
                endpoint=mat_endpoint,
                token=api_token
            )
            
            # Extract data
            clients = response.get("data", {}).get("clients", [])
            
            if not clients:
                print("No clients found")
                break
            
            # Store client-level data from first request
            if not client_data:
                client_data = {
                    "clientFiscalYear": clients[0].get("clientFiscalYear"),
                    "parentClientId": clients[0].get("parentClientId"),
                    "clientId": clients[0].get("clientId"),
                    "clientName": clients[0].get("clientName"),
                    "clientProfileId": clients[0]["clientProfiles"][0].get("clientProfileId") if clients[0].get("clientProfiles") else None,
                    "clientAuditYear": clients[0]["clientProfiles"][0].get("clientAuditYear") if clients[0].get("clientProfiles") else None
                }
            
            client_profiles = clients[0].get("clientProfiles", [])
            engagements_connection = client_profiles[0].get("engagements", {}) if client_profiles else {}
            edges = engagements_connection.get("edges", [])
            page_info = engagements_connection.get("pageInfo", {})
            
            if total_count is None and "totalCount" in engagements_connection:
                total_count = engagements_connection["totalCount"]
                print(f"Total engagements available: {total_count}")
            
            # Extract engagement nodes from edges
            engagements = [edge["node"] for edge in edges]
            
            print(f"Retrieved {len(engagements)} engagements")
            all_engagements.extend(engagements)
            total_str = f" / {total_count}" if total_count is not None else ""
            print(f"Total engagements so far: {len(all_engagements)}{total_str}")
            
            # Update pagination state
            has_next_page = page_info.get("hasNextPage", False)
            cursor = page_info.get("endCursor")
            
            print(f"Has next page: {has_next_page}")
            
        except Exception as e:
            print(f"Error on request {request_count}: {str(e)}")
            raise
    
    print(f"\n=== Fetch Complete ===")
    print(f"Total API requests: {request_count}")
    print(f"Total engagements retrieved: {len(all_engagements)}")
    
    # Reconstruct the full response
    return {
        "data": {
            "clients": [{
                "clientFiscalYear": client_data["clientFiscalYear"],
                "parentClientId": client_data["parentClientId"],
                "clientId": client_data["clientId"],
                "clientName": client_data["clientName"],
                "clientProfiles": [{
                    "clientProfileId": client_data["clientProfileId"],
                    "clientAuditYear": client_data["clientAuditYear"],
                    "engagements": all_engagements
                }]
            }]
        }
    }


# ===================================================================
# HELPER FUNCTION: MAKE GRAPHQL REQUEST
# ===================================================================

def make_graphql_request(
    query: str,
    variables: Dict[str, Any],
    endpoint: str = None,
    token: str = None
) -> Dict[str, Any]:
    """
    Make a GraphQL request to MAT API.
    
    Args:
        query: GraphQL query string
        variables: Query variables
        endpoint: GraphQL endpoint URL (if None, uses env var MAT_GRAPHQL_ENDPOINT)
        token: API token (if None, uses env var MAT_API_TOKEN)
        
    Returns:
        GraphQL response data
    """
    
    # Get endpoint and token from environment if not provided
    endpoint = endpoint or os.getenv("MAT_GRAPHQL_ENDPOINT")
    token = token or os.getenv("MAT_API_TOKEN")
    
    if not endpoint:
        raise ValueError("MAT GraphQL endpoint not provided. Set MAT_GRAPHQL_ENDPOINT environment variable.")
    
    if not token:
        raise ValueError("MAT API token not provided. Set MAT_API_TOKEN environment variable.")
    
    # Prepare headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        # Add any other required headers
    }
    
    # Prepare request body
    payload = {
        "query": query,
        "variables": variables
    }
    
    # Make request
    response = requests.post(endpoint, json=payload, headers=headers)
    
    # Check response status
    if not response.ok:
        raise Exception(f"GraphQL request failed: {response.status_code} {response.reason}\n{response.text}")
    
    # Parse response
    result = response.json()
    
    # Check for GraphQL errors
    if "errors" in result:
        raise Exception(f"GraphQL errors: {json.dumps(result['errors'], indent=2)}")
    
    return result


# ===================================================================
# USAGE EXAMPLES
# ===================================================================

def example1_offset_based():
    """Example 1: Using offset-based pagination"""
    try:
        result = fetch_all_engagements_offset_based(
            client_id="0008005369",
            fiscal_year="2025",
            page_size=500
        )
        
        print("\nFinal result:")
        print(f"Client: {result['data']['clients'][0]['clientName']}")
        print(f"Total engagements: {len(result['data']['clients'][0]['clientProfiles'][0]['engagements'])}")
        
        # Save to file
        with open("result_offset.json", "w") as f:
            json.dump(result, f, indent=2)
        print("Saved to result_offset.json")
        
    except Exception as e:
        print(f"Failed to fetch engagements: {str(e)}")


def example2_cursor_based():
    """Example 2: Using cursor-based pagination"""
    try:
        result = fetch_all_engagements_cursor_based(
            client_id="0008005369",
            fiscal_year="2025",
            page_size=500
        )
        
        print("\nFinal result:")
        print(f"Client: {result['data']['clients'][0]['clientName']}")
        print(f"Total engagements: {len(result['data']['clients'][0]['clientProfiles'][0]['engagements'])}")
        
        # Save to file
        with open("result_cursor.json", "w") as f:
            json.dump(result, f, indent=2)
        print("Saved to result_cursor.json")
        
    except Exception as e:
        print(f"Failed to fetch engagements: {str(e)}")


def example3_process_chunks():
    """Example 3: Process engagements in chunks"""
    result = fetch_all_engagements_offset_based(
        client_id="0008005369",
        fiscal_year="2025",
        page_size=500
    )
    
    engagements = result["data"]["clients"][0]["clientProfiles"][0]["engagements"]
    
    # Process in smaller chunks
    chunk_size = 100
    for i in range(0, len(engagements), chunk_size):
        chunk = engagements[i:i + chunk_size]
        print(f"Processing engagements {i} to {i + len(chunk) - 1}")
        # Process chunk...


if __name__ == "__main__":
    # Run example 1 (offset-based)
    print("=" * 60)
    print("EXAMPLE 1: OFFSET-BASED PAGINATION")
    print("=" * 60)
    example1_offset_based()
    
    # Run example 2 (cursor-based)
    print("\n" + "=" * 60)
    print("EXAMPLE 2: CURSOR-BASED PAGINATION")
    print("=" * 60)
    example2_cursor_based()
